from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from models import User, Document
from schemas import DocumentResponse
from auth import get_current_user
from utils.pdf import save_uploaded_pdf, is_allowed_file
from dependencies import get_db

router = APIRouter(prefix="/documents", tags=["문서"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    file_type: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """PDF 파일 업로드 및 저장"""
    try:
        # 파일 확장자 확인
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF 파일만 업로드 가능합니다."
            )
        
        # PDF 저장
        file_info = save_uploaded_pdf(
            file=file,
            user_id=current_user.id,
            file_type=file_type
        )
        
        # 데이터베이스에 저장
        db_document = Document(
            filename=file_info["filename"],
            filepath=file_info["filepath"],
            original_filename=file.filename,
            file_size=file_info["size"],
            file_type=file_type,
            page_count=file_info.get("page_count"),
            user_id=current_user.id
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return db_document
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 사용자의 업로드된 문서 목록 조회"""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 문서 조회"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다."
        )
    
    return document

