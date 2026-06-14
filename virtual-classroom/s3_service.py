import os
import uuid
from werkzeug.utils import secure_filename
import boto3
from dotenv import load_dotenv

load_dotenv()

# Check if AWS variables are present
USE_S3 = all([
    os.getenv('AWS_ACCESS_KEY_ID'),
    os.getenv('AWS_SECRET_ACCESS_KEY'),
    os.getenv('AWS_S3_BUCKET'),
    os.getenv('AWS_REGION')
])

LOCAL_UPLOAD_FOLDER = os.path.join('static', 'uploads')

# Ensure local directories exist if not using S3
if not USE_S3:
    os.makedirs(os.path.join(LOCAL_UPLOAD_FOLDER, 'thumbnails'), exist_ok=True)
    os.makedirs(os.path.join(LOCAL_UPLOAD_FOLDER, 'materials'), exist_ok=True)

def get_s3_client():
    """Returns an authenticated boto3 S3 client if config is present."""
    if USE_S3:
        return boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
    return None

def upload_file(file_storage, folder='materials'):
    """Uploads a file to S3 or saves locally as a fallback.
    Returns: (file_key, file_url)
    """
    if not file_storage or file_storage.filename == '':
        return None, None
        
    original_filename = secure_filename(file_storage.filename)
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(original_filename)
    unique_filename = f"{name}_{unique_id}{ext}"
    
    file_key = f"{folder}/{unique_filename}"
    
    if USE_S3:
        s3 = get_s3_client()
        bucket = os.getenv('AWS_S3_BUCKET')
        region = os.getenv('AWS_REGION')
        try:
            # Upload to AWS S3
            s3.upload_fileobj(
                file_storage,
                bucket,
                file_key,
                ExtraArgs={
                    'ContentType': file_storage.content_type
                }
            )
            # URL format
            file_url = f"https://{bucket}.s3.{region}.amazonaws.com/{file_key}"
            return file_key, file_url
        except Exception as e:
            print(f"AWS S3 Upload failed (using local fallback instead): {e}")
            # fall through to local upload fallback

    # Local fallback
    local_path = os.path.join(LOCAL_UPLOAD_FOLDER, folder, unique_filename)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    # Save file content locally
    file_storage.seek(0)
    file_storage.save(local_path)
    
    # Return local relative static URL
    file_url = f"/static/uploads/{folder}/{unique_filename}"
    return file_key, file_url
