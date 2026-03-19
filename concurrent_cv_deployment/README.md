# Concurrent Computer Vision Task Deployment on Azure ML

This repository contains code required to deploy a mock Computer Vision (CV) model to an Azure ML Managed Online Endpoint that fulfills these specific concurrency requirements:
- **1 Worker Process**: Configured with `WORKER_COUNT=1`.
- **Concurrent Request Handling**: Main thread accepts requests concurrently without blocking.
- **Simultaneous Processing**: Heavy CPU-bound CV jobs execute truly in parallel across multiple CPU cores.

## Architecture

1. **Single Worker (`WORKER_COUNT=1`)**: 
   We configure Azure ML to spawn exactly one main Python worker process in `deployment.yml`.

2. **Multi-threaded Worker (`GUNICORN_CMD_ARGS: "--threads 4"`)**: 
   The default Azure ML HTTP inference server uses Flask and Gunicorn. Because Flask is natively synchronous, it does not support `async def`. Instead, we get concurrency by telling Gunicorn to use multiple threads. The single main worker process efficiently distributes incoming HTTP requests to these threads concurrently.

3. **Simultaneous Processing on Multiple Cores (`ProcessPoolExecutor`)**: 
   Computer Vision tasks are mostly CPU-bound. If run natively in the main event loop, they would block everything due to the Global Interpreter Lock (GIL). 
   To execute the CV task asynchronously and on a separate CPU core, we instantiate a `ProcessPoolExecutor` inside our script's `init()` function with multiple worker limits.

## How it works (Execution flow)

1. **Request 1** hits the endpoint. 
   - Gunicorn assigns it to Thread #1. Thread #1 offloads the 10-second CV job to the `ProcessPoolExecutor`, and calls `.result()` to wait.
   - Thread #1 is now explicitly blocked, but the Python GIL is released by the ProcessPool.
2. **Request 2** arrives simultaneously. 
   - The main HTTP process instantly accepts Request 2 and assigns it to Thread #2.
   - Thread #2 offloads Request 2 to a second available core on the process pool, and waits.
3. **Simultaneous Compute**: Both CV jobs run in full parallelism on separate CPU cores completely independently of the HTTP worker threads.
4. **Resolution**: As each CV job completes (after 10s), their respective Gunicorn thread unblocks, and the server returns the HTTP response back to the client natively. 

## Files structure

- `src/score.py`: Main scoring logic with async loops and `ProcessPoolExecutor`.
- `deployment.yml`: Azure ML managed endpoint deployment configuration.
- `endpoint.yml`: Naming and authentication properties for the online endpoint deployment.
- `environment.yml`: Dependency spec mapping required libraries.
- `deploy.sh`: Bash script to automate the full deployment process.
- `test_concurrency.py`: Python script to validate that your endpoint can process requests concurrently.

## Deployment Automation

To eliminate manual steps, a `deploy.sh` script is provided which creates the endpoint, the deployment, and prints out your secure Authentication Key and Scoring URI at the very end.

```bash
# Ensure the script is executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```
*(Deployments typically take 5 to 15 minutes as Azure ML provisions the node and builds the environment.)*

## Validation & Testing

Once your endpoint is officially live and you have your **Scoring URI** and **Authentication Key** (provided to you at the end of the deployment script), you can run the concurrency test check.

1. Open `test_concurrency.py`.
2. Update the `ENDPOINT_URL` and `AUTH_KEY` variables with your live credentials.
3. Run the validaton script:

```bash
python test_concurrency.py
```

**What the test does**:
The client script will use multithreading to fire exactly **4 HTTP requests** at the exact same moment. Each request triggers a 10-second CV job on the server.
- If they were processed sequentially by the single worker, the test would conclude in **40 seconds**.
- Because our architecture routes them asynchronously to the `ProcessPoolExecutor`, they process in parallel on multiple cores, resulting in the script completing in **~10 seconds**. The script will automatically confirm success or failure!
