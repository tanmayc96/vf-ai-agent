#!/bin/bash

# Configuration
PROJECT_ID="vodafone-network-461305"
SERVICE_NAME="ngni-agent-service"
REGION="europe-west1" # Default region, feel free to change
USER_ACCOUNT="tanmay@chandramohit.altostrat.com" # Added for authentication

echo "============================================================"
echo "Deployment Script: $SERVICE_NAME to Cloud Run"
echo "Project ID: $PROJECT_ID"
echo "Region:     $REGION"
echo "============================================================"

# Check for gcloud installation
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI is not installed."
    echo "Please visit https://cloud.google.com/sdk/docs/install or install it first."
    exit 1
fi

# optional: Check if authenticated and set project
if [ -n "$USER_ACCOUNT" ]; then
    echo "Setting account to $USER_ACCOUNT..."
    gcloud config set account "$USER_ACCOUNT"
fi

echo "Setting active project to $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

# Read .env file to pass as environment variables to Cloud Run
# gcloud run deploy --set-env-vars expects a comma-separated list of KEY=VALUE
ENV_VARS=""
if [ -f .env ]; then
    echo "Found .env file. Processing environment variables..."
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Ignore comments and empty lines
        [[ "$line" =~ ^#.* ]] && continue
        [[ -z "$line" ]] && continue
        
        # Parse KEY=VALUE
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            
            # Trim whitespace
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            
            # Escape commas if value contains it (Cloud Run might be sensitive, usually fine or needs careful escaping)
            # For simplicity, just append
            if [ -n "$key" ]; then
                # Handle cases where value has spaces or special chars
                # We should append KEY="VALUE" or simply KEY=VALUE
                # Cloud Run CLI parses commas as separator, so we need to be careful
                # For basic env vars (like PROJECT, LOCATION), it works perfectly.
                ENV_VARS+="$key=$value,"
            fi
        fi
    done < .env
    # Remove trailing comma
    ENV_VARS=${ENV_VARS%,}
fi

echo "------------------------------------------------------------"
if [ -n "$ENV_VARS" ]; then
    echo "Deploying with environment variables from .env..."
    gcloud run deploy "$SERVICE_NAME" \
        --source . \
        --project "$PROJECT_ID" \
        --region "$REGION" \
        --allow-unauthenticated \
        --set-env-vars "$ENV_VARS"
else
    echo "Deploying without additional environment variables..."
    gcloud run deploy "$SERVICE_NAME" \
        --source . \
        --project "$PROJECT_ID" \
        --region "$REGION" \
        --allow-unauthenticated
fi

echo "------------------------------------------------------------"
echo "Deployment initiated."
echo "If this is the first time, Cloud Run might ask to enable APIs."
echo "Please follow any interactive prompts if they appear."
echo "============================================================"

# --- Alternative Manual Method (in comments for reference) ---
# For reference, if you prefer explicit build and push (e.g. for CI/CD):
# 
# 1. Create Artifact Registry repository:
#    gcloud artifacts repositories create docker-images --repository-format=docker --location=$REGION --project=$PROJECT_ID
# 
# 2. Build and push image:
#    gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/docker-images/$SERVICE_NAME:latest .
# 
# 3. Deploy from image:
#    gcloud run deploy $SERVICE_NAME --image $REGION-docker.pkg.dev/$PROJECT_ID/docker-images/$SERVICE_NAME:latest --region $REGION --allow-unauthenticated
# -------------------------------------------------------------
