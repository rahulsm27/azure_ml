from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential
import os

def register_dummy_model():
    print("Authenticating with Azure...")
    # DefaultAzureCredential will automatically use Azure CLI login,
    # environment variables, or VS Code Azure Account extension.
    credential = DefaultAzureCredential()

    # NOTE: Set these variables or environment variables before running!
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

    # Define the dummy model
    dummy_model_path = "./models/dummy_model"
    model_name = "concurrent-cv-dummy-model"

    print(f"Registering local path '{dummy_model_path}' as model name '{model_name}'...")
    
    dummy_model = Model(
        path=dummy_model_path,
        name=model_name,
        description="A dummy CV model weights container for testing concurrent scoring deployments.",
        tags={"task": "Computer Vision", "status": "dummy_test"}
    )

    # Execute the registration
    registered_model = ml_client.models.create_or_update(dummy_model)
    
    print("\nSUCCESS!")
    print(f"Model ID:      {registered_model.id}")
    print(f"Model Name:    {registered_model.name}")
    print(f"Model Version: {registered_model.version}")

if __name__ == "__main__":
    register_dummy_model()
