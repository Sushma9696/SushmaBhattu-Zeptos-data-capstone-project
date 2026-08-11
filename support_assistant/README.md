
# Zepto GenAI Customer Support Assistant

This is a small GenAI support project built for **Zepto** policies. It helps answer customer questions about delivery, return, cancellation, membership, and support. 

It uses **LangGraph** to route questions, **ChromaDB** with `sentence-transformers` for searching local documents, and **FastAPI** to serve the API.

By default, this service runs completely **offline in mock mode (`MOCK_LLM=1`)**. You do not need any API key, payment card, or internet connection to run or test this project.

------------------------------------------------------------------------------------------------------------------------------------

## How the Pipeline Works (Architecture)

The complete application works in 4 simple steps:

[ User asks a Question ]

│

▼

[ FastAPI /ask ]

│

▼

┌────────────────────────────────────────────────────────────┐
│ LangGraph Pipeline                                         │

│                                                            │

│  [ Step 1: classify_intent ]                               │

│       │                                                    │

│       ├──► Check keyword (policy vs general question)      │

│       │                                                    │

│       ├─────────────────────────┐                          │

│       ▼                         ▼                          │

│  [ policy_question ]     [ general_question ]              │

│       │                         │                          │

│       ▼                         ▼                          │

│  [ Step 2: retrieve ]    [ Step 3: direct_answer ]         │

│  ├── Fetch top 3 chunks         └── Return simple canned   │

│  └── Prepare answer                 message                │

└───────────────────────┬────────────────────────────────────┘

│

▼

[ Valid JSON Output ]


### Stage Details:

1. **Ingestion (`ingestion.py`)**: Reads all 8 policy files from the `docs/` folder, creates embeddings locally using the free `all-MiniLM-L6-v2` model, and saves them into ChromaDB.
2. **Embedding (`ingestion.py` & `graph.py`)**: Converts document sentences and user questions into vector numbers locally on your system.
3. **Retrieval (`graph.py`)**: Searches ChromaDB to find the top 3 most matching document chunks for policy questions. *This search step always runs for real locally.*
4. **Generation (`graph.py` & `app.py`)**:
   - `classify_intent`: Checks if the question has policy keywords like "delivery", "refund", "cancel", etc.
   - `retrieve_and_answer`: Takes the top matching chunk and formats the output.
   - `direct_answer`: Returns a basic friendly response for general questions.
   - Output is sent in exact JSON format with `answer`, `sources`, and `confidence`.

---------------------------------------------------------------------------------------------------------------------------------------

## MOCK_LLM Toggle Details

The project has a single switch called `MOCK_LLM`:

| Feature | Default Baseline (`MOCK_LLM=1` or unset) | Optional Extension (`MOCK_LLM=0`) |
| :--- | :--- | :--- |
| **Intent Classification** | Simple keyword checking (looks for words like *delivery*, *refund*, *cancel*, etc.). | Calls Groq LLM API to check intent. |
| **Document Retrieval** | Runs **real** ChromaDB search locally. | Runs **real** ChromaDB search locally. |
| **Policy Answer** | Returns canned output: `Based on the retrieved context: <top text>`. | Calls Groq LLM to generate proper answer using prompt template. |
| **General Question** | Returns: `"I can only answer questions about Zepto policies right now."` | Calls Groq LLM directly without document search. |
| **JSON Schema** | Directly generated in Python code with `confidence: 1.0`. | Validates LLM output with Pydantic; retries up to 2 times if format is wrong. |

-----------------------------------------------------------------------------------------------------------------------------------------

## How to Run the Project locally

### Method 1: Using Python Directly

1. **Open terminal and go to the folder**:
   ```bash
   cd support_assistant
Create and activate virtual environment:

Bash
python -m venv venv
On Windows: .\venv\Scripts\activate
Install required packages:

Bash
pip install -r requirements.txt
Run ingestion (saves documents to ChromaDB):

Bash
python ingestion.py
Start the FastAPI server:

Bash
uvicorn app:app --host 0.0.0.0 --port 7860
Method 2: Using Docker
Build Docker image:

Bash
docker build -t zepto-support .
Run Docker container:

Bash
docker run -p 7860:7860 zepto-support
Now open http://localhost:7860 in your browser or test via curl.

Output Examples (Tested in Default Mock Mode)
Here are actual test results run locally in default mock mode:

Example 1: Policy Question (Triggers Document Search)
Command:

Bash

curl.exe -X POST "http://127.0.0.1:7860/ask" `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"What is the return policy for damaged items?\"}'
  
JSON Output Received:

JSON
{
  "answer": "Based on the retrieved context: Grocery and perishable items may be reported for a return within 24 hours of delivery if damaged, spoiled, or incorrect; non-perishable packaged items may be returned within 7 days of delivery in unop",
  "sources": [
    "doc_02_chunk1",
    "doc_06_chunk1",
    "doc_05_chunk1"
  ],
  "confidence": 1.0
}


Example 2: General Question (Triggers Direct Response)
Command:

Bash

curl.exe -X POST "http://127.0.0.1:7860/ask" `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"What is the capital of India?\"}'
  
JSON Output Received:

JSON
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}

Optional: Running with Real Groq LLM
If you want to test with a real LLM, get a free key from console.groq.com and run:

Bash

export MOCK_LLM=0
export GROQ_API_KEY="your_actual_groq_api_key_here"
uvicorn app:app --host 0.0.0.0 --port 7860