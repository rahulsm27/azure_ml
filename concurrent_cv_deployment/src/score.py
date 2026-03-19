import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor

# Initialize logger for endpoint
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# We use ThreadPoolExecutor because Azure ML dynamically wraps score.py as 'entry_module',
# which breaks Python's ProcessPool pickling. Heavy CV libraries (PyTorch, OpenCV, ONNX) 
# natively release the Python GIL during computation, meaning ThreadPoolExecutor will still
# successfully evaluate them purely in parallel across multiple CPU cores!
executor = None

def init():
    """
    Called once when the container starts.
    We initialize the ProcessPoolExecutor here.
    """
    global executor
    
    # Initialize thread pool with desired number of concurrent worker threads.
    # We are simulating multiple cores, so max_workers=4 is used as an example.
    executor = ThreadPoolExecutor(max_workers=4)
    logger.info("ThreadPoolExecutor initialized with 4 max workers.")

def cv_task(raw_data):
    """
    This function simulates a heavy Computer Vision task.
    It runs in a separate thread from the pool, avoiding blocking the main request receiver.
    """
    # Parse json data (Optional based on your actual data payload format)
    logger.info("Starting CV task in separate background thread...")
    
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
    
    # Offload the blocking CPU-bound CV task to the thread pool so we don't hog the main thread.
    # By calling .result(), this specific HTTP worker thread blocks and waits for the CPU core to finish.
    # However, because we configured Gunicorn with multiple threads in deployment.yml, 
    # the main HTTP process is instantly free to dispatch the next request to another instance simultaneously!
    future = executor.submit(cv_task, raw_data)
    result = future.result()
    
    logger.info("Task finished! Returning result to the client.")
    return result
