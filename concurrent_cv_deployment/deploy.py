from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model,
    Environment,
    CodeConfiguration,
    OnlineRequestSettings,
)
from azure.identity import DefaultAzureCredential
import os

def deploy_concurrent_cv_endpoint():
    print("Authenticating with Azure...")
    # DefaultAzureCredential will automatically pick up Azure CLI login
    credential = DefaultAzureCredential()

    # NOTE: Set these variables before running!
    # e.g., export AZURE_SUBSCRIPTION_ID="your_subs_id"
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "<YOUR_SUBSCRIPTION_ID>")
    resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "<YOUR_RESOURCE_GROUP>")
    workspace_name = os.environ.get("AZURE_WORKSPACE_NAME", "<YOUR_WORKSPACE_NAME>")

    print(f"Connecting to workspace: {workspace_name}...")
    try:
        ml_client = MLClient(
            credential, 
            subscription_id, 
            resource_group, 
            workspace_name
        )
    except Exception as e:
        print(f"Failed to initialize MLClient. Check credentials and workspace info.\n{e}")
        return

    endpoint_name = "my-concurrent-cv-endpoint"
    deployment_name = "cv-concurrent-deployment"

    # ==========================================================
    # 1. Create the Endpoint
    # ==========================================================
    print(f"\n[1/3] Creating/Updating Online Endpoint '{endpoint_name}'...")
    endpoint = ManagedOnlineEndpoint(
        name=endpoint_name,
        auth_mode="key",
    )
    
    # begin_create_or_update returns an LROPoller, we call .result() to wait for completion
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("Endpoint created successfully.")

    # ==========================================================
    # 2. Setup the Environment and Code
    # ==========================================================
    env = Environment(
        name="cv-concurrent-env",
        image="mcr.microsoft.com/azureml/minimal-ubuntu20.04-py38-cpu-inference:latest",
        conda_file="./environment.yml",
    )

    code_config = CodeConfiguration(
        code="./src",
        scoring_script="score.py"
    )

    # ==========================================================
    # 3. Create the Deployment
    # ==========================================================
    # Note: We are deploying the dummy model folder we created earlier.
    print(f"\n[2/3] Creating/Updating Online Deployment '{deployment_name}'... This may take 5-15 minutes.")
    deployment = ManagedOnlineDeployment(
        name=deployment_name,
        endpoint_name=endpoint_name,
        model=Model(path="./models/dummy_model/"),
        environment=env,
        code_configuration=code_config,
        instance_type="Standard_F4s_v2",
        instance_count=1,
        # Configures Azure ML load balancer to forward up to 4 concurrent requests to this instance
        request_settings=OnlineRequestSettings(
            max_concurrent_requests_per_instance=4,
            request_timeout_ms=60000  # Sets timeout to 60 seconds (since CV task takes 10s minimum)
        ),
        # Here is where we inject the multi-threading logic to enable concurrency!
        environment_variables={
            "WORKER_COUNT": "1",
            "GUNICORN_CMD_ARGS": "--threads 4"
        }
    )
    
    # Start the deployment creation and wait
    ml_client.online_deployments.begin_create_or_update(deployment).result()
    print("Deployment created successfully.")

    # ==========================================================
    # 4. Route Traffic
    # ==========================================================
    print(f"\n[3/3] Routing 100% of traffic to deployment '{deployment_name}'...")
    endpoint.traffic = {deployment_name: 100}
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()

    # ==========================================================
    # 5. Fetch Credentials for Testing
    # ==========================================================
    endpoint_obj = ml_client.online_endpoints.get(endpoint_name)
    keys = ml_client.online_endpoints.get_keys(endpoint_name)
    
    print("\n==========================================================")
    print(" Deployment Successfully Completed!")
    print("==========================================================")
    print("SCORING URI: ", endpoint_obj.scoring_uri)
    print("AUTH KEY:    ", keys.primary_key)
    print("\nUpdate your `test_concurrency.py` with these credentials to validate!")

if __name__ == "__main__":
    deploy_concurrent_cv_endpoint()
