from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from models import Document
from schemas import DocumentResponse
from utils.pdf import save_uploaded_pdf, is_allowed_file
from dependencies import get_db

router = APIRouter(prefix="/documents", tags=["문서"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    file_type: str = "pdf",
    db: Session = Depends(get_db)
):
    """PDF 파일 업로드 및 저장 (인증 없음)"""
    try:
        # 파일 확장자 확인
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF 파일만 업로드 가능합니다."
            )
        
        # PDF 저장 (user_id 없이)
        file_info = save_uploaded_pdf(
            file=file,
            user_id=None,
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
            user_id=None
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
    db: Session = Depends(get_db)
):
    """업로드된 문서 목록 조회 (인증 없음)"""
    documents = db.query(Document).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """특정 문서 조회 (인증 없음)"""
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다."
        )
    
    return document

