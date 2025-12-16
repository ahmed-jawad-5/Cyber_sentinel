# server/rag_service.py
import faiss
from server.rag_runner import RAGRunner

# Initialize RAGRunner once
rag_runner = RAGRunner()

def run_rag_on_packet(features: dict) -> str:
    query = " | ".join(f"{k}: {v}" for k, v in features.items())
    # Embed
    q_emb = rag_runner.emb_model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    # Retrieve top-K
    D, I = rag_runner.index.search(q_emb, rag_runner.top_k)
    retrieved_docs = [rag_runner.metadata[i] for i in I[0] if i < len(rag_runner.metadata)]
    if not retrieved_docs:
        return "No similar flows found"
    prompt = rag_runner.build_prompt_with_context(query, retrieved_docs, detailed=True)
    return rag_runner.llm.generate(prompt, max_new_tokens=200)
