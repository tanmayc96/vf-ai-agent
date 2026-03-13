import os 
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

def get_rag_tool():
    """Initializes the Vertex AI RAG Retrieval tool."""
    #corpus_name="projects/vf-grp-aib-dev-ngi-sbx-alpha/locations/europe-west1/ragCorpora/4611686018427387904"
    rag_project = os.getenv("RAG_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", "vf-grp-aib-dev-ngi-sbx-alpha"))
    rag_location = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
    rag_corpus_id = os.getenv("RAG_CORPUS_ID", "4611686018427387904")

    corpus_name = f"projects/{rag_project}/locations/{rag_location}/ragCorpora/{rag_corpus_id}"

    if not corpus_name:
        print("Warning: RAG_CORPUS link is missing")

    return VertexAiRagRetrieval(
        name="rag_retrieval_tool",
        description=("Search the financial data for trends and analysis"),
        rag_resources=[
            rag.RagResource(
                rag_corpus=corpus_name
            )
        ],
        similarity_top_k=10, 
        vector_distance_threshold=0.6,
    )