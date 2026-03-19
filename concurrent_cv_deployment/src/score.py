import json
import time
import asyncio
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

async def run(raw_data):
    """
    The main thread handles incoming HTTP scoring requests concurrently.
    By using `async def`, Azure ML's serving framework treats this as a coroutine.
    """
    logger.info("Received prediction request. Submitting to process pool...")
    
    # Get the current asyncio event loop (the main thread's loop handling the HTTP web server)
    loop = asyncio.get_running_loop()
    
    # Offload the blocking CPU-bound CV task to the process pool.
    # We `await` its completion. This is critical:
    # 1) The HTTP request connection stays open.
    # 2) BUT, the main thread's event loop is *freed immediately*. 
    # 3) The main thread can concurrently accept and dispatch the next incoming request
    #    while this particular task is crunching away on another CPU core.
    result = await loop.run_in_executor(executor, cv_task, raw_data)
    
    logger.info("Task finished! Returning result to the client.")
    return result
