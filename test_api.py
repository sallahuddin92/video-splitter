import subprocess
import time
import urllib.request
import urllib.error
import json
import sys
import os
import signal

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

def run_test():
    print("Starting FastAPI server...")
    # Start server in separate process
    server_process = subprocess.Popen(
        ["venv/bin/uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for server to be ready
        health_url = "http://127.0.0.1:8000/docs"
        if not wait_for_server(health_url):
            print("Server failed to start.")
            stdout, stderr = server_process.communicate()
            print("STDOUT:", stdout.decode())
            print("STDERR:", stderr.decode())
            return False
            
        print("Server is up. Sending POST request...")
        
        api_url = "http://127.0.0.1:8000/process-video"
        data = {
            "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "start_time": 0,
            "end_time": 5
        }
        
        req = urllib.request.Request(
            api_url, 
            data=json.dumps(data).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                print(f"Response Code: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                
                if response.status == 200 and "video/mp4" in response.headers.get('Content-Type', ''):
                    content = response.read()
                    print(f"Received {len(content)} bytes of video data.")
                    print("SUCCESS: API End-to-End Test Passed.")
                    return True
                else:
                    print("FAILURE: Invalid response.")
                    return False
                    
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            print(e.read().decode())
            return False
            
    finally:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    if run_test():
        sys.exit(0)
    else:
        sys.exit(1)
