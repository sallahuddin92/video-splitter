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
    print("\n--- Testing Analyze Endpoint ---")
    api_url = "http://127.0.0.1:8000/analyze"
    data = {
        # Using a longer video sample to ensure we get > 1 segment
        # Big Buck Bunny is ~10 min. 
        "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "chunk_duration": 60 
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
                if body['total_duration'] > 0 and len(body['segment_list']) > 0:
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

def test_process():
    print("\n--- Testing Process (Split & Zip) Endpoint ---")
    api_url = "http://127.0.0.1:8000/process"
    data = {
        # Using smaller sample for speed
        "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "chunk_duration": 5
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
            
            if response.status == 200 and "application/zip" in ctype:
                content = response.read()
                print(f"Received {len(content)} bytes of ZIP data.")
                
                # Verify zip header
                if content.startswith(b'PK'):
                    print("SUCCESS: Valid ZIP header detected.")
                    return True
                else:
                    print("FAILURE: Content is not a valid zip.")
                    return False
            else:
                print("FAILURE: Invalid response.")
                return False
                    
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
        return False

def run_test():
    server_process = subprocess.Popen(
        ["venv/bin/uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        health_url = "http://127.0.0.1:8000/docs"
        if not wait_for_server(health_url):
            print("Server failed to start.")
            return False
            
        if not test_analyze():
             return False
        
        if not test_process():
            return False
            
        print("\nALL TESTS PASSED.")
        return True
            
    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    if run_test():
        sys.exit(0)
    else:
        sys.exit(1)
