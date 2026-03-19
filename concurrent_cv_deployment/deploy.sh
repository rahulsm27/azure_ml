#!/bin/bash

# Exit on any error
set -e

# Configuration 
ENDPOINT_NAME="my-concurrent-cv-endpoint"
RESOURCE_GROUP="your-resource-group" # Optional: if not set in defaults
WORKSPACE="your-workspace-name"      # Optional: if not set in defaults

echo "=========================================================="
echo " Starting Deployment: Concurrent CV Task on Azure ML"
echo "=========================================================="

# Step 1: Create the endpoint
# This creates a logical endpoint (the URL) where traffic can be routed.
echo -e "\n[1/3] Creating the Online Endpoint..."
az ml online-endpoint create -f endpoint.yml

# Step 2: Create the deployment
# This actually provisions the compute, builds the environment, and runs your code.
# The '--all-traffic' flag automatically routes 100% of the endpoint's traffic to this new deployment.
echo -e "\n[2/3] Creating the Online Deployment (This step usually takes 5-15 minutes)..."
az ml online-deployment create -f deployment.yml --all-traffic

# Step 3: Retrieve connection credentials
echo -e "\n[3/3] Retrieving Endpoint Credentials..."

SCORING_URI=$(az ml online-endpoint show --name $ENDPOINT_NAME --query scoring_uri -o tsv)
AUTH_KEY=$(az ml online-endpoint get-credentials --name $ENDPOINT_NAME --query primaryKey -o tsv)

echo ""
echo "=========================================================="
echo " Deployment Successfully Completed!"
echo "=========================================================="
echo -e "\nYour Endpoint is Live at:"
echo "SCORING URI: $SCORING_URI"
echo "AUTH KEY:    $AUTH_KEY"
echo ""
echo "To test your concurrency script locally against the live endpoint,"
echo "update 'test_concurrency.py' with the variables above."
