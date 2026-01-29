import subprocess
import time
import urllib.request
import urllib.error
import json
import sys
import os

def wait_for_server(url, retries=20, delay=1):
    for i in range(retries):
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return True
        except ConnectionRefusedError:
            pass
        except urllib.error.URLError:
            pass
        time.sleep(delay)
    return False

def test_analyze():
    print("\n--- Testing Analyze Endpoint (Universal) ---")
    api_url = "http://127.0.0.1:8000/analyze"
    data = {
        "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "chunk_duration": 5,
        "platform": "fb"
    }
    
    req = urllib.request.Request(
        api_url, 
        data=json.dumps(data).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                body = json.loads(response.read().decode())
                print(f"SUCCESS: {body}")
                if 'segments' in body and len(body['segments']) > 0 and 'title' in body:
                    return True
            else:
                print(f"FAILURE: Status {response.status}")
                return False
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_process_segment():
    print("\n--- Testing Process Segment (Streaming) Endpoint ---")
    api_url = "http://127.0.0.1:8000/process-segment"
    data = {
        "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "start": 0,
        "end": 5,
        "segment_index": 1
    }
    
    req = urllib.request.Request(
        api_url, 
        data=json.dumps(data).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Response Code: {response.status}")
            ctype = response.headers.get('Content-Type', '')
            print(f"Content-Type: {ctype}")
            
            if response.status == 200 and "video/mp4" in ctype:
                # Read first chunk to ensure stream is working
                chunk = response.read(1024)
                if len(chunk) > 0:
                    print(f"SUCCESS: Received initial bytes of MP4 stream.")
                    return True
                else:
                    print("FAILURE: Empty stream.")
                    return False
            else:
                print("FAILURE: Invalid response content-type or status.")
                return False
                    
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
        return False

def run_test():
    # Since we are running against the RELOADING server from previous steps
    # We might not need to start it, but to be clean/safe we usually would.
    # However user has a running uvicorn process.
    # We will try to connect to the existing server first.
    
    try:
        health_url = "http://127.0.0.1:8000/docs"
        if not wait_for_server(health_url, retries=5):
            print("Server not accessible. Please ensure it is running.")
            return False
            
        if not test_analyze():
             return False
        
        if not test_process_segment():
            return False
            
        print("\nALL TESTS PASSED.")
        return True
            
    except Exception as e:
        print(f"Test runner error: {e}")
        return False

if __name__ == "__main__":
    if run_test():
        sys.exit(0)
    else:
        sys.exit(1)
