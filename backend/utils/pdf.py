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


def compress_pdf(pdf_path: str, output_path: str = None, quality: int = 85) -> str:
    """
    PDF 압축 (PyPDF2 사용, Pillow는 이미지 처리용)
    
    Args:
        pdf_path: 원본 PDF 경로
        output_path: 저장할 경로 (None이면 원본 경로에 compressed_ 접두사 추가)
        quality: 압축 품질 (1-100, 낮을수록 압축률 높음)
    
    Returns:
        저장된 파일 경로
    """
    try:
        from PyPDF2 import PdfReader, PdfWriter
        
        if output_path is None:
            # 원본 경로에 compressed_ 접두사 추가
            path_obj = Path(pdf_path)
            output_path = str(path_obj.parent / f"compressed_{path_obj.name}")
        
        # PDF 읽기
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # 모든 페이지 복사 (압축 옵션 적용)
        for page in reader.pages:
            # 페이지 압축 (PyPDF2의 기본 압축 사용)
            page.compress_content_streams()
            writer.add_page(page)
        
        # 메타데이터 복사
        if reader.metadata:
            writer.add_metadata(reader.metadata)
        
        # 압축된 PDF 저장
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path
    
    except ImportError:
        # PyPDF2가 없으면 원본 파일 그대로 반환
        if output_path is None:
            output_path = pdf_path
        import shutil
        shutil.copy2(pdf_path, output_path)
        return output_path
    except Exception as e:
        raise ValueError(f"PDF 압축 실패: {str(e)}")


def compress_pdf_with_pillow(pdf_path: str, output_path: str = None, dpi: int = 150) -> str:
    """
    PDF를 이미지로 변환하여 압축 (Pillow 사용)
    주의: 이 방법은 PDF를 이미지로 변환하므로 텍스트 검색이 불가능합니다.
    
    Args:
        pdf_path: 원본 PDF 경로
        output_path: 저장할 경로 (None이면 원본 경로에 compressed_ 접두사 추가)
        dpi: 이미지 해상도 (낮을수록 파일 크기 작음, 기본 150)
    
    Returns:
        저장된 파일 경로
    """
    try:
        from PIL import Image
        from pdf2image import convert_from_path
        
        if output_path is None:
            path_obj = Path(pdf_path)
            output_path = str(path_obj.parent / f"compressed_{path_obj.name}")
        
        # PDF를 이미지로 변환
        images = convert_from_path(pdf_path, dpi=dpi)
        
        # 이미지를 PDF로 저장 (Pillow 사용)
        if images:
            images[0].save(
                output_path,
                "PDF",
                resolution=dpi,
                save_all=True,
                append_images=images[1:] if len(images) > 1 else []
            )
        
        return output_path
    
    except ImportError:
        # pdf2image나 Pillow가 없으면 기본 압축 사용
        return compress_pdf(pdf_path, output_path)
    except Exception as e:
        raise ValueError(f"PDF 이미지 변환 압축 실패: {str(e)}")


def save_uploaded_pdf(
    file, 
    user_id: int = None,
    file_type: str = "pdf",
    compress: bool = True
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
    
    # PDF 압축 (선택사항)
    if compress:
        try:
            compressed_path = compress_pdf(str(filepath))
            # 압축된 파일이 더 작으면 교체
            if Path(compressed_path).stat().st_size < filepath.stat().st_size:
                import shutil
                shutil.move(compressed_path, filepath)
        except Exception:
            # 압축 실패 시 원본 파일 사용
            pass
    
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
    
    # 파일 크기 확인 (압축 후)
    file_size = filepath.stat().st_size
    
    return {
        "filename": unique_filename,
        "filepath": str(filepath),
        "size": file_size,
        "page_count": page_count
    }

