import os

from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 500 * 1024  # 500 KB
MIN_LOGO_PX = 50


def validate_image_upload(file):
    """Valida extensión, peso, que sea imagen real y dimensión mínima."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f"Extensión no permitida: {ext}. Usa JPG, PNG o WEBP.")

    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError("Máximo 500 KB por imagen.")

    try:
        from PIL import Image

        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)
        img = Image.open(file)
        w, h = img.size
        if w < MIN_LOGO_PX or h < MIN_LOGO_PX:
            raise ValidationError(f"El logo debe medir al menos {MIN_LOGO_PX}×{MIN_LOGO_PX} px.")
        file.seek(0)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc
