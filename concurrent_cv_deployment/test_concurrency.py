import time
import json
import urllib.request
import urllib.error
import concurrent.futures

# --- CONFIGURATION ---
# Replace with your actual endpoint URL. 
# If testing locally via Azure ML CLI v2 ('az ml online-deployment create --local ...'),
# it usually exposes a local server on port 5001 or similar. Check your 'az ml' logs.
ENDPOINT_URL = "http://localhost:5001/score"

# If testing against the live Azure ML endpoint, provide the Bearer token/key here.
AUTH_KEY = "" 

def send_request(req_id):
    """
    Sends a single HTTP POST request to the inference endpoint and measures the response time.
    """
    print(f"[{time.strftime('%H:%M:%S')}] Request {req_id} sent...")
    
    # Prepare the payload
    data = json.dumps({"data": "mock_image_data_or_tensor"}).encode("utf-8")
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
    }
    
    if AUTH_KEY:
        headers["Authorization"] = f"Bearer {AUTH_KEY}"
        
    req = urllib.request.Request(ENDPOINT_URL, data=data, headers=headers, method="POST")
    
    try:
        start_time = time.time()
        with urllib.request.urlopen(req) as response:
            result_data = response.read().decode("utf-8")
            status_code = response.getcode()
            
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"[{time.strftime('%H:%M:%S')}] Request {req_id} completed in {elapsed:.2f} seconds. Result: {result_data}")
        return elapsed
        
    except urllib.error.URLError as e:
        print(f"[{time.strftime('%H:%M:%S')}] Request {req_id} failed: {e}")
        return None

def main(num_requests=4):
    """
    Simulates multiple clients sending requests to the server simultaneously.
    If concurrency is working, 4 requests (each taking 10s on the server) 
    should complete in ~10 seconds total, rather than 40 seconds.
    """
    print(f"Starting concurrency validation test with {num_requests} simultaneous requests...")
    print(f"Targeting: {ENDPOINT_URL}\n")
    
    start_time = time.time()
    
    # We use a client-side ThreadPoolExecutor to fire the HTTP requests in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        # Submit all requests immediately
        futures = [executor.submit(send_request, i+1) for i in range(num_requests)]
        
        # Wait for all client requests to finish
        concurrent.futures.wait(futures)
            
    total_time = time.time() - start_time
    
    print("\n" + "="*40)
    print("           TEST SUMMARY")
    print("="*40)
    print(f"Total time elapsed for {num_requests} requests: {total_time:.2f} seconds")
    
    # The server CV task takes 10 seconds. 
    # Sequential execution: 4 * 10 = 40 seconds.
    # Concurrent execution: ~10-12 seconds.
    if total_time < (num_requests * 10) * 0.5: 
        print("SUCCESS! \nCalculations ran concurrently in parallel on the server.")
        print("The total time is significantly less than sequential execution.")
    else:
        print("WARNING! \nIt took longer than expected. Requests might be queuing or processing sequentially.")
        print("Ensure 'WORKER_COUNT' is 1 and the ProcessPoolExecutor has enough cores.")

if __name__ == "__main__":
    main(num_requests=4)
