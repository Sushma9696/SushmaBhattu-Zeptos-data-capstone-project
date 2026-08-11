import os
import json
from typing import List, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from groq import Groq

from ingestion import initialize_vector_store
from prompts import STRUCTURED_PROMPT_TEMPLATE

# --- Pydantic Schema ---
class SupportResponseSchema(BaseModel):
    answer: str = Field(description="The final answer string")
    sources: List[str] = Field(default_factory=list, description="IDs of source chunks used")
    confidence: float = Field(default=1.0, description="Confidence score between 0 and 1")

# --- LangGraph State ---
class SupportGraphState(TypedDict):
    query: str
    intent: Optional[str]
    retrieved_chunks: List[dict]
    final_output: Optional[dict]

# Keywords for mock intent classification
POLICY_KEYWORDS = [
    "delivery", "return", "refund", "membership", 
    "tracking", "cancel", "gift card", "support hours"
]

# Initialize Vector DB
collection = initialize_vector_store()

def is_mock_mode() -> bool:
    mock_env = os.environ.get("MOCK_LLM", "1").strip().lower()
    return mock_env in ["1", "true", "yes"]

# Node 1: Classify Intent
def classify_intent(state: SupportGraphState) -> SupportGraphState:
    query = state["query"]
    
    if is_mock_mode():
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in POLICY_KEYWORDS):
            intent = "policy_question"
        else:
            intent = "general_question"
    else:
        # Optional Real LLM Path (Groq)
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        prompt = f"Classify this query as 'policy_question' or 'general_question'. Respond with ONLY the label.\nQuery: {query}"
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        label = res.choices[0].message.content.strip().lower()
        intent = "policy_question" if "policy" in label else "general_question"

    state["intent"] = intent
    return state

# Node 2: Retrieve & Answer (Policy Questions)
def retrieve_and_answer(state: SupportGraphState) -> SupportGraphState:
    query = state["query"]
    
    # Retrieval ALWAYS runs for real
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    retrieved_chunks = []
    if results and results.get("documents"):
        docs = results["documents"][0]
        ids = results["ids"][0]
        for doc_id, doc_text in zip(ids, docs):
            retrieved_chunks.append({"id": doc_id, "text": doc_text})

    state["retrieved_chunks"] = retrieved_chunks

    if is_mock_mode():
        top_snippet = retrieved_chunks[0]["text"][:200] if retrieved_chunks else "No relevant policy found."
        sources = [c["id"] for c in retrieved_chunks]
        
        output = SupportResponseSchema(
            answer=f"Based on the retrieved context: {top_snippet}",
            sources=sources,
            confidence=1.0
        )
        state["final_output"] = output.model_dump()
    else:
        # Optional Real LLM Path with retry logic
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        context_str = "\n\n".join([f"ID: {c['id']}\nText: {c['text']}" for c in retrieved_chunks])
        prompt = STRUCTURED_PROMPT_TEMPLATE.format(context=context_str, query=query)
        
        attempts = 0
        max_retries = 2
        validated_output = None
        current_prompt = prompt

        while attempts <= max_retries:
            try:
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": current_prompt}],
                    temperature=0.1
                )
                raw_text = res.choices[0].message.content.strip()
                parsed_json = json.loads(raw_text)
                validated_output = SupportResponseSchema(**parsed_json)
                break
            except Exception as e:
                attempts += 1
                if attempts > max_retries:
                    validated_output = SupportResponseSchema(
                        answer="Error generating grounded response following required schema.",
                        sources=[c["id"] for c in retrieved_chunks],
                        confidence=0.0
                    )
                else:
                    current_prompt += f"\n\nSystem Notice: Your previous output failed JSON validation with error: {str(e)}. Please produce ONLY valid JSON matching the exact schema."

        state["final_output"] = validated_output.model_dump()

    return state

# Node 3: Direct Answer (General Questions)
def direct_answer(state: SupportGraphState) -> SupportGraphState:
    query = state["query"]
    
    if is_mock_mode():
        output = SupportResponseSchema(
            answer="I can only answer questions about Zepto policies right now.",
            sources=[],
            confidence=1.0
        )
        state["final_output"] = output.model_dump()
    else:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Answer concisely: {query}"}]
        )
        output = SupportResponseSchema(
            answer=res.choices[0].message.content.strip(),
            sources=[],
            confidence=0.8
        )
        state["final_output"] = output.model_dump()
        
    return state

# Conditional Router Function
def route_intent(state: SupportGraphState) -> str:
    return state["intent"]

# Build State Graph
builder = StateGraph(SupportGraphState)
builder.add_node("classify_intent", classify_intent)
builder.add_node("retrieve_and_answer", retrieve_and_answer)
builder.add_node("direct_answer", direct_answer)

builder.set_entry_point("classify_intent")
builder.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "policy_question": "retrieve_and_answer",
        "general_question": "direct_answer"
    }
)
builder.add_edge("retrieve_and_answer", END)
builder.add_edge("direct_answer", END)

workflow = builder.compile()