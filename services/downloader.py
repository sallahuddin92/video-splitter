import yt_dlp
import logging
import ffmpeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_video_url(url: str) -> str:
    """
    Extracts the direct video URL from a Facebook/Instagram/TikTok link using yt-dlp.
    Returns the direct URL string.
    """
    ydl_opts = {
        'format': 'best',  # Get best quality
        'quiet': True,
        'no_warnings': True,
        'simulate': True, # Do not download, just extract info
        'forceurl': True,
        # Use a generic user agent to avoid detection/blocking
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Extracting info for URL: {url}")
            info = ydl.extract_info(url, download=False)
            
            # yt-dlp returns the direct url in 'url' field for extracting info
            if 'url' in info:
                return info['url']
            else:
                raise ValueError("Could not find direct video URL in extraction results.")
                
    except Exception as e:
        logger.error(f"Error extracting video URL: {str(e)}")
        raise e

import os
import tempfile

def get_cookie_file():
    """
    Checks for YOUTUBE_COOKIES env var. if present, writes to temp file and returns path.
    """
    cookies_content = os.environ.get("YOUTUBE_COOKIES")
    if not cookies_content:
        return None
    
    # Create a temp file
    try:
        fd, path = tempfile.mkstemp(suffix=".txt", text=True)
        with os.fdopen(fd, 'w') as f:
            f.write(cookies_content)
        return path
    except Exception as e:
        logger.error(f"Failed to create cookie file: {e}")
        return None

def get_video_info(url: str):
    """
    Extracts video metadata (duration, title, etc) + direct URL.
    Returns a dict with 'duration' (seconds) and 'url'.
    """
    cookie_file = get_cookie_file()
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
        'forceurl': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'geo_bypass': True,
        'force_ipv4': True,
        'quiet': True,
    }
    
    if cookie_file:
        logger.info(f"Using cookies from environment variable")
        ydl_opts['cookiefile'] = cookie_file

    # List of client configurations to try in order
    client_strategies = [
        ['android'],
        ['ios'],
        ['web'],
        ['tv'],
        ['mweb']
    ]

    for attempt, clients in enumerate(client_strategies):
        logger.info(f"Attempt {attempt+1}/{len(client_strategies)} using clients: {clients}")
        
        ydl_opts.update({
            'extractor_args': {
                'youtube': {
                    'player_client': clients,
                    'skip': ['dash', 'hls']
                }
            }
        })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    logger.info(f"Success with clients: {clients}")
                    duration = info.get('duration')
                    # Fallback for duration
                    if not duration:
                         try:
                             probe = ffmpeg.probe(url)
                             duration = float(probe['format']['duration'])
                         except:
                             duration = 0
                             
                    return {
                        'url': info.get('url'),
                        'duration': duration,
                        'title': info.get('title', 'video')
                    }
                    
        except Exception as e:
            logger.warning(f"Failed with clients {clients}: {e}")
            continue

    # If all attempts fail
    logger.error("All extraction strategies failed.")
    return {"title": "Error", "duration": 0, "url": None}
