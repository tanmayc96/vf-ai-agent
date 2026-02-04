# NGNI Agent

This repo contains the NGNI agent implementation using the [Agent Development Kit](https://github.com/google/adk-python) (ADK).

## Getting Started

1.  **Prerequisites:**

    *   Python 3.9+ and [Poetry](https://python-poetry.org/docs/#installation) installed.
    *   Access to Google Cloud (Vertex AI).

2.  **Running the Agent:**

    *   Navigate to the agent's directory.
    
3. **Configuration:**
    * Env file setup
        * Copy example env file `cp env.example .env`
        * Add values for following variables in the `.env` file
            * `GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT>`
            * `GOOGLE_CLOUD_LOCATION=<YOUR_LOCATION>`
   
    * **BigQuery Setup**
     * If the agent will access BigQuery table, you should modify the following 
        * BigQuery DATASET_ID should be under `.env` in `DATASET_ID`
        * BigQuery TABLE_ID should be under `.env` in `TABLE_ID`

    * **Other Configuration:**
        * You can change Gemini Model by changing `MODEL` under `.env`
        * `DISABLE_WEB_DRIVER` when set to `1`, will enable you to run unit tests. See `Unit Tests` section below for details. **NOTE** keep this flag to 0 by default when not testing.


## Using the Agent

This section provides general guidance on how to run, test, evaluate, and potentially deploy the agent.

Here's a general workflow you can expect:

1.  **Navigate to the Agent Directory:** Open your terminal and change into the agent's main directory:
    ```bash
    cd ngni-agent
    ```
2.  **Review the Agent's README:** Open the `README.md` file within this directory. It will contain:
    *   A detailed overview of the agent's purpose and architecture.
    *   Specific prerequisites (e.g., API keys, cloud services, database setup).

3.  **Setup and Configuration:**
    *   **Prerequisites:** Ensure you've met the general prerequisites listed in the main "Getting Started" section *and* any specific prerequisites mentioned in the agent's README.
    *   **Dependencies:** Install the agent's specific Python dependencies using Poetry (this command is usually run from the agent's main directory):
        ```bash
        make install
        ```
    *   **Environment Variables:** Most agents require configuration via environment variables. Copy the `.env.example` file to `.env` within the agent's directory and populate it with your specific values (project IDs, etc.). Consult the agent's README for details on required variables.

4.  **Running the Agent Locally:**
    *   Agents can typically be run locally for testing and interaction using the ADK CLI or ADK Dev UI. The specific command might vary slightly.
    *   **CLI:** Often involves running `make adk-run .` from within the agent's *core code* directory.
        ```bash
        # Example
        make adk-run
        ```
    *   **ADK Dev UI:** Often involves running `make adk-web .` from the agent's *main* directory.
        ```bash
        # Example
        make adk-web
        ```
        Then, open the `http://127.0.0.1:8080/` in your browser and select the agent from the dropdown menu.

5.  **Evaluating the Agent:**
    *  To Evaluate the agent run `make adk-eval`
    *  You have to provide a json file describing the expected interaction with the agent so that the `eval` module can compare against it. An example data can be found in `eval/data/eval_data1.evalset.json` 

## Architecture & Core Features

### 1. Multi-Agent Orchestration
The agent uses a **Root Agent** to coordinate three specialized sub-agents:
-   **RAG Agent**: Extracts strategic mandates and financial goals from internal PDF strategy documents.
-   **BigQuery Agent**: Queries structured network and commercial data.
-   **Search Agent**: Enriches internal data with external market context (competitors, funding, local news).

### 2. Data Categories
The agent strictly categorizes data into three buckets to ensure precise querying:
-   **External Data (Context)**: `berlin_external_foundation` (Demographics, Geography).
-   **Vodafone Data (Performance)**: `vf_commercial_data` (Market Share, ARPU), `vf_network_performance` (Latency, Signal).
-   **Quadrant Data (Strategy)**: `berlin_final_quadrants`, `berlin_quadrants_ml_results` (Strategic alignment scores).

### 3. Ranked Output & Reasoning
The agent does not just list data; it **ranks areas** based on strategic fit.
-   **Output Format**: A JSON list of `ranked_areas`.
-   **Ranking Logic**: Areas are ranked (1-N) based on a composite score derived from commercial and network performance.
-   **Reasoning**: Each ranked item includes a specific "Reasoning" field explaining *why* it is ranked there (e.g., "High Growth Potential + Low Churn Risk").

### 4. Verbose Reporting
For transparency, the agent shares **Intermediate Findings** from each sub-agent (RAG, DB, Search) before presenting the final synthesis. This allows users to verify sources and understand the decision-making process.

### 5. Guardrails
-   **Strict Filtering**: Automatically ignores records with `NULL` municipality codes or "Unknown" names.
-   **Generic Name Exclusion**: Filters out generic names like "District Area" to ensure only valid municipalities are reported.

## Directory Structure of Agents
The agent is organized as follows:

```bash
├── ngni-agent
│   ├── ngni_agent/                         # Folder for root agent 
│   │   ├── shared_libraries/               # Folder contains helper functions for tools
│   │   ├── sub_agents/                     # Folder for each sub agent
│   │   │   ├── bigquery/                   # BigQuery sub-agent
│   │   │   ├── rag_agent/                  # RAG sub-agent
│   │   │   ├── search_agent/               # Search sub-agent
│   │   │   │   ├── tools/                  # tools folder for the subagent
│   │   │   │   ├── agent.py                # core logic of the sub agent
│   │   │   │   └── prompts.py              # prompt of the subagent
│   │   ├── __init__.py                     # Initializes the agent
│   │   ├── tools/                          # Contains the code for tools used by the router agent
│   │   ├── agent.py                        # Contains the core logic of the agent
│   │   ├── prompts.py                      # Contains the prompts for the agent
│   ├── deployment/                         # Deployment to Agent Engine
│   ├── eval/                               # Folder containing the evaluation method
│   ├── tests/                              # Folder containing unit tests for tools
│   ├── .env.example                        # Store agent specific env variables
│   ├── pyproject.toml                      # Project configuration
│   ├── Makefile                            # Define Commands to run  
│   └── README.md                           # Provides an overview of the agent
```

#### Directory Breakdown

1.  **`ngni_agent/` (Core Agent Code)**: 
    *   This directory contains the core logic of the agent.
    *   **`shared_libraries/`**: (Optional) Contains code that is shared among multiple sub-agents.
    *   **`sub_agents/`**: Contains the definitions and logic for sub-agents.
        *   Each sub-agent has its own directory (e.g., `bigquery/`, `rag_agent/`, `search_agent/`).
        *   **`tools/`**: Contains any custom tools specific to the sub-agent.
        *   **`agent.py`**: Defines the sub-agent's behavior, including its model, tools, and instructions.
        *   **`prompts.py`**: Contains the prompts used to guide the sub-agent's behavior.
    *   **`__init__.py`**: An initialization file that imports the `agent.py` from the folder for marking the `ngni_agent` directory as a Python package.
    *   **`tools/`**: Contains any custom tools used by the main agent.
    *   **`agent.py`**: Defines the main agent's behavior, including its sub-agents, model, tools, and instructions.
    *   **`prompts.py`**: Contains the prompts used to guide the main agent's behavior.

2.  **`pyproject.toml`**

    *   Contains project metadata, dependencies, and build system configuration.
    *   Managed by Poetry for dependency management.


## Creating a Custom Agent:
To create your custom agent and run it locally, you will have to update the agent logic:
* For the root (main) agent, you will need to update the logic inside `ngni_agent/agent.py` and for instructions given to the LLM you will need to modify `ngni_agent/prompts.py`. 
* For the subagents you will need to create/modify as many subfolders as the subagents required. For each subagent, you will need to create/modify `sub_agents/<sub_agent_name>/agent.py` and `sub_agents/<sub_agent_name>/prompts.py` (ex: `sub_agents/bigquery/agent.py`)

## Deploying the Agent to non-live:
   
* Need to create/modify `Dockerfile`
* You need to modify the configuration variables in `cloudbuild/image-buildnl.yaml` depending on the environment.

## API Usage

The agent exposes a REST API compliant with Cloud Run deployment requirements.

### Query Endpoint

**URL**: `/query`
**Method**: `POST`
**Content-Type**: `application/json`

**Request Body:**

**Request Body:**

```json
{
  "query": "Your question here",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

**Response:**

```json
{
  "response": "Agent's detailed response..."
}
```

### Running Locally

To run the API server locally:

1.  **Setup Environment:**
    Ensure your `.env` file is created and populated as described in the **Configuration** section above.

2.  **Install Dependencies:**
    ```bash
    poetry install
    ```

3.  **Start the Server:**
    ```bash
    poetry run python main.py
    ```
    Or using the FastAPI CLI:
    ```bash
    poetry run fastapi dev main.py
    ```
    The server will start on `http://0.0.0.0:8080`.

4.  **Test the Endpoint:**
    You can test the API using `curl`:

    ```bash
    curl -X POST "ADK_URL/query" \
         -H "Content-Type: application/json" \
         -d '{"query": "What are the top ranked areas in Berlin?", "session_id": "session_abc"}'
    ```
    curl -X POST "http://0.0.0.0:8080/query" \
         -H "Content-Type: application/json" \
         -d '{"query": "What are the top ranked areas in Berlin?", "session_id": "session_abc"}'
