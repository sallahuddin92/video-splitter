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

def get_video_info(url: str):
    """
    Extracts video metadata (duration, title, etc) + direct URL.
    Returns a dict with 'duration' (seconds) and 'url'.
    """
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
        'forceurl': True,
        # 'user_agent': 'Mozilla/5.0 ...' # Deprecated in favor of client emulation
        'extractor_args': {
            'youtube': {
                'player_client': ['tv', 'android_creator', 'android', 'ios'],
                'skip': ['dash', 'hls']
            }
        },
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'geo_bypass': True,
        'force_ipv4': True,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Extracting metadata for URL: {url}")
            info = ydl.extract_info(url, download=False)

            if not info:
                logger.error("Extraction failed: No info returned")
                return {"title": "Error", "duration": 0, "url": None}

            duration = info.get('duration')
            
            # Fallback: Use ffprobe if yt-dlp fails to get duration (common for direct URLs)
            if not duration:
                try:
                    logger.info("yt-dlp missing duration, trying ffprobe...")
                    probe = ffmpeg.probe(url)
                    duration = float(probe['format']['duration'])
                except Exception as e:
                    logger.warning(f"ffprobe failed to get duration: {e}")
                    duration = 0

            return {
                'url': info.get('url'),
                'duration': duration,
                'title': info.get('title', 'video')
            }
                
    except Exception as e:
        logger.error(f"Error extracting video metadata: {str(e)}")
        raise e
