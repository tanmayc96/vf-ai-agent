# NGNI Agent Technical Documentation

## Overview

The NGNI (Next Generation Network Insights) Agent is a specialized AI assistant designed to help network engineers and business analysts. It combines network performance data from BigQuery, strategic insights from internal documents (RAG), and external market context from Google Search to provide comprehensive answers.

## Architecture

The agent follows a hierarchical architecture with a **Root Agent** orchestrating three specialized **Sub-Agents**.

### Root Agent (`ngni_agent`)
*   **Model**: `gemini-2.5-flash`
*   **Role**: Orchestrator. It receives user queries and delegates tasks to the appropriate sub-agent based on the nature of the request.
*   **Definition**: `ngni_agent/agent.py`
*   **Tools**:
    *   `call_rag_agent`: Delegates to the RAG Agent for document-based strategic insights.
    *   `call_db_agent`: Delegates to the Database Agent for structured network data.
    *   `call_search_agent`: Delegates to the Search Agent for external information.

### Sub-Agents

#### 1. Database Agent (`db_agent`)
*   **Directory**: `ngni_agent/sub_agents/bigquery/`
*   **Role**: Retrieves structured network performance data and KPI metrics.
*   **Model**: `gemini-2.5-flash`
*   **Tools**:
    *   `query_bigquery`: Executes SQL queries against BigQuery.
    *   `run_bigquery_validation`: Validates SQL queries before execution.
*   **Configuration**:
    *   Uses `NL2SQL_METHOD` (default: "BASELINE") to determine the SQL generation strategy.
    *   Schema information is dynamically injected into the instructions.

#### 2. RAG Agent (`rag_agent`)
*   **Directory**: `ngni_agent/sub_agents/rag_agent/`
*   **Role**: Extracts insights from unstructured data like strategy reports and PDFs.
*   **Model**: `gemini-2.5-flash`
*   **Tools**:
    *   `get_rag_tool`: Connects to a Vector Search or Vertex AI Search datastore to retrieve relevant document chunks.

#### 3. Search Agent (`search_agent`)
*   **Directory**: `ngni_agent/sub_agents/search_agent/`
*   **Role**: Provides external market context, competitor analysis, and news.
*   **Model**: `gemini-2.5-flash`
*   **Tools**:
    *   `google_search`: Performs Google Search queries.

## Configuration

The agent is configured via environment variables and the `callback_context` state.

### Environment Variables (`.env`)

| Variable | Description | Required | Example |
| :--- | :--- | :--- | :--- |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | Yes | `vf-grp-aib-dev-ngi-sbx-alpha` |
| `GOOGLE_CLOUD_LOCATION` | GCP Region | Yes | `europe-west1` |
| `MODEL` | Gemini Model ID | No | `gemini-2.5-flash` |
| `DATASET_ID` | BigQuery Dataset ID | If using DB | `network_data` |
| `TABLE_ID` | BigQuery Table ID | If using DB | `performance_metrics` |
| `NL2SQL_METHOD` | SQL Generation Method | No | `BASELINE` |
| `DISABLE_WEB_DRIVER` | Disable specific tools for testing | No | `0` or `1` |

### Database Settings
The `setup_before_agent_call` hook initializes the database settings in the agent's state:
*   `use_database`: Defaults to "BigQuery".
*   `bq_ddl_schema`: The schema of the target BigQuery table is retrieved and added to the context.

## Development

### Directory Structure
```
ngni-agent/
├── ngni_agent/                 # Root agent package
│   ├── agent.py                # Root agent definition
│   ├── sub_agents/             # Sub-agent packages
│   │   ├── bigquery/           # Database agent
│   │   ├── rag_agent/          # RAG agent
│   │   └── search_agent/       # Search agent
│   └── shared_libraries/       # Shared utilities
├── pyproject.toml              # Dependencies (Poetry)
└── README.md                   # Quickstart guide
```

### Adding a New Sub-Agent
1.  Create a new directory in `ngni_agent/sub_agents/`.
2.  Define the sub-agent in `agent.py` within that directory.
3.  Register any necessary tools.
4.  Import and add the sub-agent (or its calling function) to the root agent's tool list in `ngni_agent/agent.py`.
