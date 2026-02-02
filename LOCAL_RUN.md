# Running NGNI Agent Locally

This guide details the steps to set up and run the NGNI Agent in a local environment.

## 1. Prerequisites

- Python 3.10+
- `pip` (Python package installer)
- Google Cloud credentials (if accessing BigQuery or Vertex AI services)

## 2. Environment Setup

### Create a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

Install the required packages. Note: The `google-adk` package is installed directly from the GitHub repository to ensure the latest version.

```bash
pip install git+https://github.com/google/adk-python.git "google-genai==1.56.0" "google-cloud-bigquery>=3.31.0,<4.0.0" "google-cloud-aiplatform[adk,agent-engines]>=1.88.0,<2.0.0" "kfp>=2.15.2" "python-dotenv" "uvicorn" "fastapi"
```

### Configuration (.env)

Ensure you have a `.env` file in the root directory. You can copy the example or create one:

```bash
cp .env.example .env  # If .env.example exists
# OR create specifically:
cat <<EOF > .env
GOOGLE_CLOUD_PROJECT=vf-grp-aib-dev-ngi-sbx-alpha
GOOGLE_CLOUD_LOCATION=europe-west1
MODEL=gemini-2.5-flash
DISABLE_WEB_DRIVER=0
EOF
```

## 3. Running the Agent

Start the FastAPI server using `python`:

```bash
# Ensure your virtual environment is activated
# source .venv/bin/activate

python main.py
```

The server will start at `http://0.0.0.0:8080`.

## 4. Verifying the Installation

You can test the agent using `curl` in a separate terminal:

```bash
curl -X POST http://localhost:8080/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Hello"}'
```

**Note on BigQuery Access:**
If you encounter "Access Denied" errors related to BigQuery on startup or query execution, the agent is designed to log a warning and proceed without the BigQuery schema. This allows for local testing of other agent capabilities (like RAG or generic queries) without full database permissions.
