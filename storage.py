import os
import logging
from typing import Optional, Tuple
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import aiofiles
import asyncio

from config import Config

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.storage_type = Config.STORAGE_TYPE
        self._setup_storage()
    
    def _setup_storage(self):
        """Setup storage based on configuration"""
        if self.storage_type == "s3":
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_REGION
            )
            self.bucket_name = Config.AWS_S3_BUCKET
        elif self.storage_type == "local":
            Path(Config.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, local_path: str, remote_filename: str) -> Tuple[bool, Optional[str]]:
        """Upload file to storage and return success status and URL"""
        try:
            if self.storage_type == "s3":
                return self._upload_to_s3(local_path, remote_filename)
            elif self.storage_type == "local":
                return self._upload_to_local(local_path, remote_filename)
            else:
                logger.error(f"Unsupported storage type: {self.storage_type}")
                return False, None
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False, None
    
    def _upload_to_s3(self, local_path: str, remote_filename: str) -> Tuple[bool, Optional[str]]:
        """Upload file to S3"""
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, remote_filename)
            
            # Generate presigned URL for download (expires in 1 hour)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': remote_filename},
                ExpiresIn=3600
            )
            
            logger.info(f"File uploaded to S3: {remote_filename}")
            return True, url
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return False, None
    
    def _upload_to_local(self, local_path: str, remote_filename: str) -> Tuple[bool, Optional[str]]:
        """Copy file to local storage"""
        try:
            remote_path = os.path.join(Config.LOCAL_STORAGE_PATH, remote_filename)
            
            # Copy file
            import shutil
            shutil.copy2(local_path, remote_path)
            
            # Generate local URL (for development)
            url = f"file://{os.path.abspath(remote_path)}"
            
            logger.info(f"File copied to local storage: {remote_path}")
            return True, url
            
        except Exception as e:
            logger.error(f"Local upload error: {e}")
            return False, None
    
    async def upload_file_async(self, local_path: str, remote_filename: str) -> Tuple[bool, Optional[str]]:
        """Async wrapper for file upload"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.upload_file, 
            local_path, 
            remote_filename
        )
    
    def delete_file(self, filename: str) -> bool:
        """Delete file from storage"""
        try:
            if self.storage_type == "s3":
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
                logger.info(f"File deleted from S3: {filename}")
            elif self.storage_type == "local":
                file_path = os.path.join(Config.LOCAL_STORAGE_PATH, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"File deleted from local storage: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[dict]:
        """Get file information"""
        try:
            if self.storage_type == "s3":
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=filename)
                return {
                    'size': response['ContentLength'],
                    'content_type': response['ContentType'],
                    'last_modified': response['LastModified']
                }
            elif self.storage_type == "local":
                file_path = os.path.join(Config.LOCAL_STORAGE_PATH, filename)
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    return {
                        'size': stat.st_size,
                        'content_type': self._get_content_type(filename),
                        'last_modified': stat.st_mtime
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file info for {filename}: {e}")
            return None
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.mp3': 'audio/mpeg',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def list_files(self, prefix: str = "") -> list:
        """List files in storage"""
        try:
            if self.storage_type == "s3":
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                return [obj['Key'] for obj in response.get('Contents', [])]
            elif self.storage_type == "local":
                storage_path = Path(Config.LOCAL_STORAGE_PATH)
                if prefix:
                    files = list(storage_path.glob(f"{prefix}*"))
                else:
                    files = list(storage_path.iterdir())
                return [f.name for f in files if f.is_file()]
            
            return []
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        try:
            if self.storage_type == "s3":
                response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
                total_size = sum(obj['Size'] for obj in response.get('Contents', []))
                file_count = len(response.get('Contents', []))
            elif self.storage_type == "local":
                storage_path = Path(Config.LOCAL_STORAGE_PATH)
                files = list(storage_path.iterdir())
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                file_count = len([f for f in files if f.is_file()])
            else:
                return {'total_size': 0, 'file_count': 0}
            
            return {
                'total_size': total_size,
                'file_count': file_count,
                'storage_type': self.storage_type
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {'total_size': 0, 'file_count': 0}

# Global storage manager instance
storage = StorageManager() 