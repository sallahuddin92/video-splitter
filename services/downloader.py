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

def get_video_info(url: str, format_id: str = None):
    """
    Extracts video metadata (duration, title, etc) + direct URL.
    Returns a dict with 'duration' (seconds) and 'url'.
    """
    cookie_file = get_cookie_file()
    
    ydl_opts = {
        # 'format': 'best', # REMOVED: restricting to 'best' breaks DASH extraction on web client
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
        # 'forceurl': True, # REMOVED: this forces format resolution which fails on DASH split streams
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
    # List of client configurations to try in order
    # 'web' client often exposes full range of formats (1080p, 4K) via DASH.
    # List of client configurations to try in order
    # 'default' uses yt-dlp internal defaults (often best for formats)
    client_strategies = [
        ['default'],
        ['web'],
        ['android'],
        ['ios'],
        ['tv'],
        ['mweb']
    ]

    for attempt, clients in enumerate(client_strategies):
        logger.info(f"Attempt {attempt+1}/{len(client_strategies)} using clients: {clients}")
        
        # Configure extractor args
        youtube_args = {
            # 'skip': ['dash', 'hls'] # Ensure DASH/HLS enabled
        }
        
        if clients != ['default']:
            youtube_args['player_client'] = clients
            
        ydl_opts.update({
            'extractor_args': {
                'youtube': youtube_args
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
                    
                    # Extract formats
                    formats = []
                    if 'formats' in info:
                        for f in info['formats']:
                            # Filter for ANY video file (webm, mp4, etc.)
                            # ffmpeg will re-encode to mp4 for output anyway.
                                # Normalize resolution availability
                                h = f.get('height') or 0
                                if h == 0:
                                    continue
                                    
                                label = f"{h}p"
                                
                                # Standard resolutions mapping
                                if 1000 <= h <= 1100: label = "1080p"
                                elif 700 <= h <= 750: label = "720p"
                                elif 450 <= h <= 500: label = "480p"
                                elif 330 <= h <= 390: label = "360p"
                                elif 220 <= h <= 270: label = "240p"
                                elif 130 <= h <= 160: label = "144p"
                                
                                if f.get('filesize'):
                                    size_mb = f.get('filesize') / (1024 * 1024)
                                    label += f" ({size_mb:.1f}MB)"
                                
                                # Mark if it's video-only
                                if f.get('acodec') == 'none':
                                    label += " (Video Only)"
                                
                                formats.append({
                                    "format_id": f.get('format_id'),
                                    "resolution": f"{f.get('width')}x{f.get('height')}",
                                    "height": h,
                                    "label": label,
                                    "ext": f.get('ext')
                                })
                    
                    # Dedup by height, keeping best quality usually at end of list
                    # Reverse to show highest first? frontend can handle sort.
                    # Let's clean up: unique by height.
                    unique_formats = {}
                    for f in formats:
                        unique_formats[f['height']] = f
                    
                    # Sort by height descending
                    sorted_formats = sorted(unique_formats.values(), key=lambda x: x['height'], reverse=True)

                    selected_url = info.get('url')
                    audio_url = None
                    
                    # If format_id is provided, find that specific stream
                    if format_id:
                        for f in info.get('formats', []):
                            if f.get('format_id') == format_id:
                                selected_url = f.get('url')
                                logger.info(f"Selected specific format: {format_id} ({f.get('height')}p)")
                                break
                    
                    # Always try to find a separate audio track (bestaudio)
                    # This is needed if the selected video stream is video-only (e.g. 1080p, 4K)
                    # We look for m4a/aac usually for better compatibility or just best audio
                    for f in info.get('formats', []):
                        if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                            # Found an audio-only stream
                            # Prefer m4a if available, else take any
                            audio_url = f.get('url')
                            if f.get('ext') == 'm4a':
                                break 
                                
                    return {
                        'url': selected_url,
                        'audio_url': audio_url,
                        'duration': duration,
                        'title': info.get('title', 'video'),
                        'formats': sorted_formats
                    }
                    
        except Exception as e:
            logger.warning(f"Failed with clients {clients}: {e}")
            continue

    # If all attempts fail
    logger.error("All extraction strategies failed.")
    return {"title": "Error", "duration": 0, "url": None}
