import yt_dlp
import os
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config import Config

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._ensure_download_dir()
        self._check_ffmpeg()
    
    def _ensure_download_dir(self):
        """Ensure download directory exists"""
        Path(Config.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("ffmpeg is available")
                self.ffmpeg_available = True
            else:
                logger.warning("ffmpeg not available, audio conversion may fail")
                self.ffmpeg_available = False
        except Exception as e:
            logger.warning(f"Could not check ffmpeg: {e}")
            self.ffmpeg_available = False
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    return None
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail'),
                    'formats': info.get('formats', [])
                }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    def download_video(self, url: str, format_type: str = "mp4", quality: str = "best") -> Tuple[bool, str, Optional[Dict]]:
        """Download video and return success status, file path, and info"""
        try:
            # Generate unique filename
            import uuid
            filename = f"{uuid.uuid4().hex}.{format_type}"
            filepath = os.path.join(Config.LOCAL_STORAGE_PATH, filename)
            
            logger.info(f"Download path: {filepath}")
            
            # Configure download options based on quality
            if format_type == "mp3":
                # Audio only
                ydl_opts = {
                    'format': 'bestaudio[ext=mp3]/bestaudio',
                    'outtmpl': filepath,
                    'quiet': False,  # Enable output for debugging
                    'no_warnings': False,  # Show warnings
                    'progress_hooks': [self._progress_hook],
                }
                
                # Add post-processor only if ffmpeg is available
                if hasattr(self, 'ffmpeg_available') and self.ffmpeg_available:
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                    logger.info("Using ffmpeg for audio conversion")
                else:
                    logger.info("ffmpeg not available, downloading raw audio")
            else:
                # Video formats
                if quality == "best":
                    format_spec = f'best[ext={format_type}]/best'
                elif quality == "hd":
                    format_spec = f'best[height<=720][ext={format_type}]/best[height<=720]'
                elif quality == "medium":
                    format_spec = f'best[height<=480][ext={format_type}]/best[height<=480]'
                else:
                    format_spec = f'best[ext={format_type}]/best'
                
                ydl_opts = {
                    'format': format_spec,
                    'outtmpl': filepath,
                    'quiet': False,  # Enable output for debugging
                    'no_warnings': False,  # Show warnings
                    'progress_hooks': [self._progress_hook],
                }
            
            logger.info(f"Starting download: {url}, format: {format_type}, quality: {quality}")
            logger.info(f"yt-dlp options: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("yt-dlp instance created, extracting info...")
                info = ydl.extract_info(url, download=True)
                logger.info(f"Download completed, info: {info.get('title') if info else 'None'}")
                
                # Get actual file path (might be different for audio)
                if format_type == "mp3":
                    actual_filepath = filepath.replace(f".{format_type}", ".mp3")
                else:
                    actual_filepath = filepath
                
                logger.info(f"Checking for file: {actual_filepath}")
                
                if os.path.exists(actual_filepath):
                    file_size = os.path.getsize(actual_filepath)
                    logger.info(f"File exists: {actual_filepath}, size: {file_size}")
                    
                    return True, actual_filepath, {
                        'title': info['title'] if info and 'title' in info else 'Unknown',
                        'duration': info['duration'] if info and 'duration' in info else 0,
                        'file_size': file_size,
                        'format': format_type,
                        'quality': quality
                    }
                else:
                    logger.error(f"Downloaded file not found: {actual_filepath}")
                    # Check if any file was created
                    import glob
                    files = glob.glob(os.path.join(Config.LOCAL_STORAGE_PATH, "*"))
                    logger.info(f"Files in download directory: {files}")
                    return False, "", None
                    
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, "", None
    
    def _progress_hook(self, d):
        """Progress hook for download monitoring"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                logger.info(f"Download progress: {percent:.1f}%")
        elif d['status'] == 'finished':
            logger.info("Download finished")
    
    async def download_video_async(self, url: str, format_type: str = "mp4", quality: str = "best") -> Tuple[bool, str, Optional[Dict]]:
        """Async wrapper for video download"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.download_video, 
            url, 
            format_type, 
            quality
        )
    
    def get_available_formats(self, url: str) -> Dict:
        """Get available formats for a video"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    return {'video': [], 'audio': []}
                formats = info.get('formats', [])
                
                available_formats = {
                    'video': [],
                    'audio': []
                }
                
                for fmt in formats:
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                        available_formats['video'].append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': fmt.get('format_note', 'Unknown'),
                            'filesize': fmt.get('filesize'),
                            'height': fmt.get('height')
                        })
                    elif fmt.get('acodec') != 'none':
                        available_formats['audio'].append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': fmt.get('format_note', 'Unknown'),
                            'filesize': fmt.get('filesize')
                        })
                
                return available_formats
                
        except Exception as e:
            logger.error(f"Error getting available formats: {e}")
            return {'video': [], 'audio': []}
    
    def cleanup_file(self, filepath: str):
        """Clean up downloaded file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up file: {filepath}")
        except Exception as e:
            logger.error(f"Error cleaning up file {filepath}: {e}")

# Global downloader instance
downloader = YouTubeDownloader() 