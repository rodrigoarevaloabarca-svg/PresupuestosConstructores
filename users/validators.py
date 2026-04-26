import os

from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB


def validate_image_upload(file):
    """Valida que el archivo sea una imagen real, de extensión permitida y ≤2 MB."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f'Extensión no permitida: {ext}. Usa JPG, PNG o WEBP.'
        )

    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError('Máximo 2 MB por imagen.')

    try:
        from PIL import Image
        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception as exc:
        raise ValidationError('El archivo no es una imagen válida.') from exc
