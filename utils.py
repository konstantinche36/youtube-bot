import re
import logging
from typing import Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def validate_youtube_url(url: str) -> bool:
    """Validate if URL is a valid YouTube URL"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False

def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    try:
        parsed_url = urlparse(url)
        
        if parsed_url.hostname in ['youtu.be', 'www.youtu.be']:
            return parsed_url.path[1:]  # Remove leading slash
        
        if parsed_url.hostname in ['youtube.com', 'www.youtube.com']:
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                return query_params.get('v', [None])[0]
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            elif parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]
        
        return None
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    current_size = float(size_bytes)
    while current_size >= 1024 and i < len(size_names) - 1:
        current_size /= 1024.0
        i += 1
    
    return f"{current_size:.1f} {size_names[i]}"

def format_duration(seconds: float) -> str:
    """Format duration in MM:SS format"""
    if not seconds:
        return "00:00"
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    
    return f"{minutes:02d}:{seconds:02d}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def is_valid_format(format_type: str) -> bool:
    """Check if format type is valid"""
    valid_formats = ['mp4', 'mp3', 'webm', 'avi', 'mov']
    return format_type.lower() in valid_formats

def is_valid_quality(quality: str) -> bool:
    """Check if quality is valid"""
    valid_qualities = ['best', 'worst', 'hd', 'medium', 'low']
    return quality.lower() in valid_qualities

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def parse_youtube_timestamp(timestamp: str) -> Optional[int]:
    """Parse YouTube timestamp (e.g., 1m30s) to seconds"""
    try:
        total_seconds = 0
        
        # Handle hours
        if 'h' in timestamp:
            hours = int(timestamp.split('h')[0])
            total_seconds += hours * 3600
            timestamp = timestamp.split('h')[1]
        
        # Handle minutes
        if 'm' in timestamp:
            minutes = int(timestamp.split('m')[0])
            total_seconds += minutes * 60
            timestamp = timestamp.split('m')[1]
        
        # Handle seconds
        if 's' in timestamp:
            seconds = int(timestamp.split('s')[0])
            total_seconds += seconds
        
        return total_seconds
    except Exception as e:
        logger.error(f"Error parsing timestamp {timestamp}: {e}")
        return None

def get_file_extension(format_type: str) -> str:
    """Get file extension for format type"""
    extensions = {
        'mp4': '.mp4',
        'mp3': '.mp3',
        'webm': '.webm',
        'avi': '.avi',
        'mov': '.mov'
    }
    return extensions.get(format_type.lower(), '.mp4')

def calculate_download_time(file_size: int, speed_mbps: float = 10.0) -> float:
    """Calculate estimated download time in seconds"""
    if speed_mbps <= 0:
        return 0
    
    # Convert file size to MB
    file_size_mb = file_size / (1024 * 1024)
    
    # Calculate time in seconds
    time_seconds = (file_size_mb / speed_mbps) * 8  # Convert Mbps to MB/s
    
    return time_seconds

def format_download_time(seconds: float) -> str:
    """Format download time in human readable format"""
    if seconds < 60:
        return f"{int(seconds)} сек"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} мин"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} ч {minutes} мин" 