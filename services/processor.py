import ffmpeg
import os
import uuid
import logging
import zipfile
import shutil
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_video(direct_url: str, start_time: int, end_time: int, output_dir: str = "temp") -> str:
    """
    Downloads and trims a video from a direct URL using ffmpeg.
    
    Args:
        direct_url: The direct URL of the video stream.
        start_time: Start time in seconds.
        end_time: End time in seconds.
        output_dir: Directory to save the processed file.
        
    Returns:
        Path to the processed video file.
    """
    
    # Ensure temp directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, filename)
    
    duration = end_time - start_time
    if duration <= 0:
        raise ValueError("End time must be greater than start time.")

    logger.info(f"Processing video: {direct_url} | Start: {start_time}, Duration: {duration}")

    try:
        # Construct ffmpeg stream
        # -ss searches to start_time
        # -t specifies duration
        # -c copy attempts to stream copy (fast, no re-encode)
        # We put -ss before input for faster seeking, but with remote URLs sometimes accurate seek is better after.
        # However, for remote files, input seeking is usually standard for trimming.
        
        # Note: 'c="copy"' might be problematic if keyframes don't align. 
        # If precision is needed, we should re-encode. The prompt implies re-encoding if precision needed.
        # Let's try re-encoding with libx264 for safety and precision, as 'copy' on random segments often leads to frozen frames at start.
        # But 'fast' was requested. Let's try copy first? No, prompt says: "or re-encode using libx264 if precision is needed."
        # Safe bet for cutting specific timestamps is re-encoding.
        
        (
            ffmpeg
            .input(direct_url, ss=start_time, t=duration)
            .output(output_path, vcodec='libx264', preset='fast', crf=23, acodec='aac')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        logger.info(f"Video processed successfully: {output_path}")
        return output_path
        
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf8') if e.stderr else str(e)}")
        raise RuntimeError(f"FFmpeg processing failed: {e.stderr.decode('utf8') if e.stderr else str(e)}")

def split_video(direct_url: str, chunk_duration: int, output_dir: str = "temp") -> str:
    """
    Downloads and splits video into chunks of `chunk_duration`.
    Zips the resulting files.
    Returns path to the .zip file.
    """
    unique_id = str(uuid.uuid4())
    work_dir = os.path.join(output_dir, unique_id)
    os.makedirs(work_dir, exist_ok=True)
    
    logger.info(f"Splitting video from {direct_url} into {chunk_duration}s chunks in {work_dir}")
    
    try:
        # Files pattern
        segment_filename = os.path.join(work_dir, "segment_%03d.mp4")
        
        # FFmpeg command to split video
        # -f segment: use segment muxer
        # -segment_time: duration of each segment
        # -reset_timestamps 1: reset timestamps for each segment so they start at 0
        # -c copy: try to copy stream for speed (fast split), but it might be inaccurate on keyframes
        # -c libx264: re-encode for precise cuts at exact times. Prompt asked for "High performance" but also "Exact how many segments". 
        # Re-encoding ensures duration accuracy but is slower.
        # "Precise cutting" usually implies re-encoding.
        
        (
            ffmpeg
            .input(direct_url)
            .output(segment_filename, f='segment', segment_time=chunk_duration, reset_timestamps=1, vcodec='libx264', preset='fast', acodec='aac')
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Create Zip
        zip_filename = f"segments_{unique_id}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(work_dir):
                for file in files:
                    if file.endswith('.mp4'):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, arcname=file)
        
        logger.info(f"Created zip file: {zip_path}")
        
        # Cleanup work dir (the folder acting as temp for segments)
        shutil.rmtree(work_dir)
        
        return zip_path

    except ffmpeg.Error as e:
        # Cleanup on fail
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        logger.error(f"FFmpeg split error: {e.stderr.decode('utf8') if e.stderr else str(e)}")
        raise RuntimeError(f"FFmpeg split failed: {e.stderr.decode('utf8') if e.stderr else str(e)}")

def stream_video_segment(direct_url: str, start: int, end: int, audio_url: str = None, original_url: str = None, format_id: str = None):
    """
    Generator that streams a specific video segment using ffmpeg.
    Yields chunks of bytes.
    
    For YouTube URLs, uses yt-dlp subprocess to handle auth properly.
    For other URLs (Facebook, etc), uses direct FFmpeg.
    """
    import subprocess
    
    duration = end - start
    if duration <= 0:
         raise ValueError("Invalid duration")

    logger.info(f"Streaming segment: {start}-{end}s from {direct_url} (Audio: {'Yes' if audio_url else 'No'})")

    # Check if this is a YouTube/googlevideo URL - they need special handling
    is_youtube = 'googlevideo.com' in direct_url or 'youtube.com' in direct_url
    
    if is_youtube and original_url:
        # Use yt-dlp to download to temp file, then ffmpeg to stream
        logger.info(f"Using yt-dlp->ffmpeg pipeline for YouTube URL")
        
        import tempfile
        
        # Build format selector
        format_str = 'best[ext=mp4]/best' if not format_id else f'{format_id}+bestaudio/best'
        
        # Create temp file for yt-dlp output
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Step 1: Download with yt-dlp to temp file
            ytdlp_cmd = [
                'yt-dlp',
                '-f', format_str,
                '--quiet',
                '--no-warnings',
                '-o', temp_path,
                '--force-overwrites',
                original_url
            ]
            
            logger.info(f"Downloading with yt-dlp to {temp_path}...")
            result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"yt-dlp error: {result.stderr}")
                # Cleanup and fallback
                os.unlink(temp_path)
                return
            
            logger.info(f"Download complete, streaming with ffmpeg...")
            
            # Step 2: Stream from temp file with ffmpeg
            stream = ffmpeg.input(temp_path, ss=start, t=duration)
            process = (
                ffmpeg
                .output(stream, 'pipe:', 
                       vcodec='libx264', preset='superfast', crf=23, 
                       acodec='aac', format='mp4', 
                       movflags='frag_keyframe+empty_moov', loglevel="error")
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            
            try:
                while True:
                    chunk = process.stdout.read(65536)
                    if not chunk:
                        break
                    yield chunk
                    
                process.stdout.close()
                process.wait()
                
                if process.returncode != 0:
                    error = process.stderr.read().decode('utf8')
                    logger.error(f"FFmpeg error: {error}")
                    
            except Exception as e:
                logger.error(f"FFmpeg streaming exception: {e}")
                process.kill()
                
        finally:
            # Always cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"Cleaned up temp file: {temp_path}")
    else:
        # For non-YouTube URLs, use direct FFmpeg (Facebook, Instagram, etc work fine)
        http_headers = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\nReferer: https://www.youtube.com/"
        
        stream = ffmpeg.input(direct_url, ss=start, t=duration, headers=http_headers)
        
        if audio_url:
            audio_stream = ffmpeg.input(audio_url, ss=start, t=duration, headers=http_headers)
            process = (
                ffmpeg
                .output(stream, audio_stream, 'pipe:', 
                       vcodec='libx264', preset='superfast', crf=23, 
                       acodec='aac', format='mp4', 
                       movflags='frag_keyframe+empty_moov', shortest=None, loglevel="error")
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
        else:
            process = (
                ffmpeg
                .output(stream, 'pipe:', 
                       vcodec='libx264', preset='superfast', crf=23, 
                       acodec='aac', format='mp4', 
                       movflags='frag_keyframe+empty_moov', loglevel="error")
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

        try:
            while True:
                chunk = process.stdout.read(65536)
                if not chunk:
                    break
                yield chunk
                
            process.stdout.close()
            process.wait()
            
            if process.returncode != 0:
                error = process.stderr.read().decode('utf8')
                logger.error(f"FFmpeg streaming error: {error}")
                
        except Exception as e:
            logger.error(f"Streaming exception: {e}")
            process.kill()
