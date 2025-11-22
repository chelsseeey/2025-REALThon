from PIL import Image
import os
from pathlib import Path
from typing import Tuple
import uuid

# 이미지 저장 디렉토리
UPLOAD_DIR = Path("uploads/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 허용된 이미지 확장자
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

# 최대 이미지 크기 (픽셀)
MAX_IMAGE_SIZE = (1920, 1920)

# 압축 품질 (JPEG: 85, PNG는 무손실)
JPEG_QUALITY = 85


def is_allowed_file(filename: str) -> bool:
    """파일 확장자가 허용된 형식인지 확인"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def compress_image(
    image_path: str,
    output_path: str = None,
    max_size: Tuple[int, int] = MAX_IMAGE_SIZE,
    quality: int = JPEG_QUALITY
) -> str:
    """
    이미지를 압축하여 저장
    
    Args:
        image_path: 원본 이미지 경로
        output_path: 저장할 경로 (None이면 원본 경로에 저장)
        max_size: 최대 이미지 크기 (너비, 높이)
        quality: JPEG 품질 (1-100)
    
    Returns:
        저장된 이미지 경로
    """
    try:
        # 이미지 열기
        with Image.open(image_path) as img:
            # RGB 모드로 변환 (RGBA, P 모드 등 처리)
            if img.mode in ("RGBA", "LA", "P"):
                # 투명도가 있는 경우 흰색 배경에 합성
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # 이미지 크기 조정 (최대 크기 초과 시)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 저장 경로 결정
            if output_path is None:
                output_path = image_path
            
            # JPEG 형식으로 저장 (압축)
            img.save(
                output_path,
                "JPEG",
                quality=quality,
                optimize=True
            )
            
            return output_path
    
    except Exception as e:
        raise ValueError(f"이미지 압축 실패: {str(e)}")


def save_uploaded_image(file, user_id: int = None) -> dict:
    """
    업로드된 이미지를 압축하여 저장
    
    Args:
        file: FastAPI UploadFile 객체
        user_id: 사용자 ID (선택사항, 디렉토리 구조화용)
    
    Returns:
        {
            "filename": 저장된 파일명,
            "filepath": 저장된 파일 경로,
            "size": 파일 크기 (bytes),
            "width": 이미지 너비,
            "height": 이미지 높이
        }
    """
    # 파일 확장자 확인
    if not is_allowed_file(file.filename):
        raise ValueError(f"허용되지 않은 파일 형식입니다. 허용 형식: {', '.join(ALLOWED_EXTENSIONS)}")
    
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
    
    # 임시 파일로 저장
    temp_path = filepath.with_suffix('.tmp')
    with open(temp_path, "wb") as f:
        content = file.file.read()
        f.write(content)
    
    # 이미지 정보 가져오기
    with Image.open(temp_path) as img:
        original_width, original_height = img.size
    
    # 이미지 압축
    compress_image(str(temp_path), str(filepath))
    
    # 임시 파일 삭제
    if temp_path.exists():
        temp_path.unlink()
    
    # 파일 크기 확인
    file_size = filepath.stat().st_size
    
    return {
        "filename": unique_filename,
        "filepath": str(filepath),
        "size": file_size,
        "width": original_width,
        "height": original_height
    }


