import os
from pathlib import Path
from typing import Optional
import uuid
import io

# PDF 저장 디렉토리
UPLOAD_DIR = Path("uploads/pdfs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {".pdf"}

# 최대 파일 크기 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def is_allowed_file(filename: str) -> bool:
    """파일 확장자가 허용된 형식인지 확인"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def compress_pdf_with_pillow(pdf_path: str, output_path: str = None) -> str:
    """
    PDF를 이미지로 변환하여 압축 (Pillow 사용)
    주의: 이 방법은 PDF를 이미지로 변환하므로 텍스트 검색이 불가능합니다.
    
    Args:
        pdf_path: 원본 PDF 경로
        output_path: 저장할 경로 (None이면 원본 경로에 저장)
    
    Returns:
        저장된 파일 경로
    """
    try:
        # PyPDF2나 pdf2image를 사용하는 것이 더 적합하지만,
        # 여기서는 Pillow로 PDF의 첫 페이지를 이미지로 변환하는 예시를 보여줍니다.
        # 실제로는 pdf2image 라이브러리를 사용하는 것을 권장합니다.
        
        # PDF를 이미지로 변환하려면 pdf2image가 필요하지만,
        # 여기서는 기본적인 저장만 수행
        if output_path is None:
            output_path = pdf_path
        
        # 실제 압축은 PyPDF2나 pypdf를 사용하는 것이 좋습니다
        # 여기서는 파일을 그대로 복사
        import shutil
        shutil.copy2(pdf_path, output_path)
        
        return output_path
    
    except Exception as e:
        raise ValueError(f"PDF 처리 실패: {str(e)}")


def save_uploaded_pdf(
    file, 
    user_id: int = None,
    file_type: str = "pdf"
) -> dict:
    """
    업로드된 PDF를 저장
    
    Args:
        file: FastAPI UploadFile 객체
        user_id: 사용자 ID (선택사항, 디렉토리 구조화용)
        file_type: 파일 타입 (pdf, answer_sheet, graded_paper 등)
    
    Returns:
        {
            "filename": 저장된 파일명,
            "filepath": 저장된 파일 경로,
            "size": 파일 크기 (bytes),
            "page_count": PDF 페이지 수 (선택사항)
        }
    """
    # 파일 확장자 확인
    if not is_allowed_file(file.filename):
        raise ValueError(f"허용되지 않은 파일 형식입니다. PDF 파일만 업로드 가능합니다.")
    
    # 파일 크기 확인
    file_content = file.file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE / 1024 / 1024}MB까지 업로드 가능합니다.")
    
    # 고유한 파일명 생성
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # 사용자별 디렉토리 생성 (선택사항)
    if user_id:
        user_dir = UPLOAD_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        filepath = user_dir / unique_filename
    else:
        filepath = UPLOAD_DIR / unique_filename
    
    # PDF 파일 저장
    with open(filepath, "wb") as f:
        f.write(file_content)
    
    # PDF 페이지 수 확인 (선택사항, PyPDF2 필요)
    page_count = None
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_content))
        page_count = len(reader.pages)
    except ImportError:
        # PyPDF2가 설치되지 않은 경우 무시
        pass
    except Exception:
        # PDF 읽기 실패 시 무시
        pass
    
    # 파일 크기 확인
    file_size = filepath.stat().st_size
    
    return {
        "filename": unique_filename,
        "filepath": str(filepath),
        "size": file_size,
        "page_count": page_count
    }

