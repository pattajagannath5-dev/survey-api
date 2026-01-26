import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
from io import BytesIO
from app.config import settings
import aiofiles

def validate_image_file(file: UploadFile) -> bool:
    """Validate image file type and size"""
    allowed_types = settings.ALLOWED_IMAGE_TYPES.split(",")
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    return True

async def save_upload_file(file: UploadFile, survey_id: str) -> tuple[str, str, int]:
    """
    Save uploaded image file and return (filename, file_path, file_size)
    """
    validate_image_file(file)
    
    # Create survey-specific upload directory
    survey_upload_dir = os.path.join(settings.UPLOAD_DIRECTORY, survey_id)
    os.makedirs(survey_upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(survey_upload_dir, unique_filename)
    
    # Read and validate image
    contents = await file.read()
    
    # Check file size (MAX_UPLOAD_SIZE_MB)
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Validate image integrity
    try:
        img = Image.open(BytesIO(contents))
        img.verify()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    return unique_filename, file_path, len(contents)

def delete_upload_file(file_path: str) -> bool:
    """Delete uploaded file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False
