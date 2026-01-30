from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from services.downloader import get_video_url, get_video_info
from services.processor import process_video, split_video, stream_video_segment
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Facebook Video Downloader & Cutter")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str
    start_time: int
    end_time: int

class AnalyzeRequest(BaseModel):
    url: str
    chunk_duration: int
    platform: str = "fb" # Optional, for future use

class ProcessSegmentRequest(BaseModel):
    url: str
    start: int
    end: int
    segment_index: int | str
    format_id: str | None = None

class ProcessRequest(BaseModel):
    url: str
    chunk_duration: int

def cleanup_file(path: str):
    """Background task to remove the file after it's sent."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleaned up file: {path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {path}: {e}")

@app.post("/process-video")
async def process_video_endpoint(request: VideoRequest, background_tasks: BackgroundTasks):
    try:
        # 1. Get direct URL
        logger.info(f"Received request for URL: {request.url}")
        direct_url = get_video_url(request.url)
        logger.info(f"Extracted Direct URL: {direct_url}")
        
        # 2. Process video (Download & Cut)
        output_path = process_video(direct_url, request.start_time, request.end_time)
        
        # 3. Return file and schedule cleanup
        filename = os.path.basename(output_path)
        
        # We use BackgroundTasks to delete the file after the response is sent
        background_tasks.add_task(cleanup_file, output_path)
        
        return FileResponse(
            path=output_path, 
            filename=filename, 
            media_type="video/mp4"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_video_endpoint(request: AnalyzeRequest):
    try:
        # Get metadata only
        info = get_video_info(request.url)
        duration = info['duration']
        title = info['title']
        
        if duration == 0:
            raise HTTPException(status_code=400, detail="Could not determine video duration.")
            
        if request.chunk_duration == 0:
            # Full video download mode
            num_segments = 1
            segments = [{
                "id": 1,
                "start": 0,
                "end": duration,
                "filename": "full_video.mp4"
            }]
        else:
            num_segments = math.ceil(duration / request.chunk_duration)
            segments = []
            
            for i in range(num_segments):
                start = i * request.chunk_duration
                end = min((i + 1) * request.chunk_duration, duration)
                segments.append({
                    "id": i + 1,
                    "start": start,
                    "end": end,
                    "filename": f"part_{i+1}.mp4"
                })
            
        return {
            "title": title,
            "total_duration": duration,
            "segments": segments,
            "formats": info.get('formats', [])
        }
        
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-segment")
async def process_segment_endpoint(request: ProcessSegmentRequest):
    try:
        # 1. Get direct URL
        info = get_video_info(request.url, request.format_id) 
        direct_url = info['url']
        if not direct_url:
             direct_url = get_video_url(request.url)

        # 2. Stream
        filename = f"video_part_{request.segment_index}.mp4"
        
        # Determine if we should pass audio_url (for high-res video-only streams)
        # We pass it if it exists. processor.py will decide how to use it.
        return StreamingResponse(
            stream_video_segment(direct_url, request.start, request.end, info.get('audio_url'), request.url, request.format_id),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Process segment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream-segment")
async def stream_segment_get(
    url: str, 
    start: int, 
    end: int, 
    segment_index: str, 
    format_id: str = None
):
    """
    GET version of process-segment to allow direct browser downloads (native progress bar).
    """
    try:
        # 1. Get direct URL
        # Note: We re-fetch info here. Caching would be better but this is safer for fresh links.
        info = get_video_info(url, format_id) 
        direct_url = info['url']
        if not direct_url:
             direct_url = get_video_url(url)

        # 2. Stream
        filename = f"video_part_{segment_index}.mp4"
        
        return StreamingResponse(
            stream_video_segment(direct_url, start, end, info.get('audio_url'), url, format_id),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Stream segment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_split_endpoint(request: ProcessRequest, background_tasks: BackgroundTasks):
    try:
        # 1. Get direct URL
        info = get_video_info(request.url) # Re-using get_video_info to get direct url securely
        direct_url = info['url']
        if not direct_url:
             # Fallback if specific extraction fails, though get_video_info wraps standard extraction
             direct_url = get_video_url(request.url)

        # 2. Split and Zip
        zip_path = split_video(direct_url, request.chunk_duration)
        
        # 3. Return file
        filename = os.path.basename(zip_path)
        background_tasks.add_task(cleanup_file, zip_path)
        
        return FileResponse(
            path=zip_path, 
            filename=filename, 
            media_type="application/zip"
        )

    except Exception as e:
        logger.error(f"Process split error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
