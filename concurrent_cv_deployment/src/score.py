import json
import time
import logging
from concurrent.futures import ProcessPoolExecutor

# Initialize logger for endpoint
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# We use ProcessPoolExecutor for CPU-bound Computer Vision tasks.
# This ensures that tasks leverage multiple CPU cores and bypass 
# the Python Global Interpreter Lock (GIL), allowing them to run 
# truly simultaneously.
executor = None

def init():
    """
    Called once when the container starts.
    We initialize the ProcessPoolExecutor here.
    """
    global executor
    
    # Initialize process pool with desired number of concurrent worker processes.
    # We are simulating multiple cores, so max_workers=4 is used as an example.
    executor = ProcessPoolExecutor(max_workers=4)
    logger.info("ProcessPoolExecutor initialized with 4 max workers.")

def cv_task(raw_data):
    """
    This function simulates a heavy Computer Vision task.
    It runs in a separate process in the pool, avoiding blocking the main event loop thread.
    """
    # Parse json data (Optional based on your actual data payload format)
    logger.info("Starting CV task in separate process worker...")
    
    # Simulate a heavy computational CV task taking exactly 10 seconds
    time.sleep(10)
    
    logger.info("CV task completed after 10 seconds.")
    
    return {
        "status": "success", 
        "message": "CV processing complete",
        "processing_time_seconds": 10
    }

def run(raw_data):
    """
    Handles incoming HTTP scoring requests concurrently.
    Because the Azure ML Inference server uses Flask natively, it does not support `async def`.
    Instead, we use Gunicorn threads (`WORKER_COUNT=1`, `--threads 4`) to achieve concurrency.
    """
    logger.info("Received prediction request. Submitting to process pool...")
    
    # Offload the blocking CPU-bound CV task to the process pool so we don't hog the GIL.
    # By calling .result(), this specific HTTP worker thread blocks and waits for the CPU core to finish.
    # However, because we configured Gunicorn with multiple threads in deployment.yml, 
    # the main HTTP process is instantly free to dispatch the next request to another thread simultaneously!
    future = executor.submit(cv_task, raw_data)
    result = future.result()
    
    logger.info("Task finished! Returning result to the client.")
    return result
