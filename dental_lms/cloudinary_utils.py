from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def upload_to_cloudinary(uploaded_file, folder, resource_type='auto'):
    if not uploaded_file:
        return ''
    if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
        raise ImproperlyConfigured('Cloudinary credentials are not configured.')

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
    result = cloudinary.uploader.upload(
        uploaded_file,
        folder=folder,
        resource_type=resource_type,
        use_filename=True,
        unique_filename=True,
        overwrite=False,
    )
    return result.get('secure_url') or result.get('url') or ''
