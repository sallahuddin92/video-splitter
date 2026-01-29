import sys
import os
import logging
from services.downloader import get_video_url
from services.processor import process_video

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ManualTest")

def test_downloader(url):
    print(f"\n--- Testing Downloader with URL: {url} ---")
    try:
        direct_url = get_video_url(url)
        print(f"SUCCESS: Extracted URL: {direct_url}")
        return direct_url
    except Exception as e:
        print(f"FAILURE: {e}")
        return None

def test_processor(direct_url, start, end):
    print(f"\n--- Testing Processor ---")
    print(f"Input: {direct_url}")
    print(f"Trim: {start}s to {end}s")
    try:
        output_path = process_video(direct_url, start, end, output_dir="test_output")
        print(f"SUCCESS: Processed file saved to {output_path}")
        # Verify file exists and has size
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print("File exists and is not empty.")
            return output_path
        else:
            print("File missing or empty.")
            return None
    except Exception as e:
        print(f"FAILURE: {e}")
        return None

if __name__ == "__main__":
    # Test Data
    # Using a reliable test video source for processor if downloader fails or for consistent testing
    # Big Buck Bunny is often used, but might be too long/large. 
    # We'll try to use the downloader first.
    
    # This is a public Facebook video implementation details video, usually safe? 
    # Actually, let's use a sample MP4 for the processor test if we can't get a FB url.
    sample_mp4 = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
    
    # 1. Test Processor directly (skipping downloader to isolate ffmpeg)
    # We verify ffmpeg works with a known valid direct URL.
    print("STEP 1: Verifying FFmpeg Processor with sample MP4...")
    output = test_processor(sample_mp4, 0, 5)
    
    if output:
        print("\nFFmpeg Processor verified successfully.")
        # Cleanup
        try:
            os.remove(output)
            print("Cleanup successful.")
        except:
            pass
    else:
        print("\nFFmpeg Processor verification FAILED.")

    # 2. Test Downloader (Optional/Interactive)
    # If a URL is passed as arg, test it.
    if len(sys.argv) > 1:
        fb_url = sys.argv[1]
        print(f"\nSTEP 2: Verifying Downloader with provided URL: {fb_url}")
        direct_url = test_downloader(fb_url)
        
        if direct_url:
            print("Downloader verified. Attempting full flow...")
            test_processor(direct_url, 0, 5)
    else:
        print("\nNo URL provided for Downloader test. Pass a Facebook URL as argument to test yt-dlp.")
