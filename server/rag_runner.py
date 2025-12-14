"""
Optimized local RAG runner
- Loads embeddings once
- Loads FAISS index + metadata
- Uses local Phi-4-mini-instruct for generation
"""

import os
import pickle
from typing import List, Dict
import faiss
from sentence_transformers import SentenceTransformer
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# -----------------------------
INDEX_DIR = "./models/rag_final/faiss_index"
PHI_MODEL_PATH = "./models/rag_final/model/Phi-4-mini-instruct"
EMBED_MODEL_PATH = "./models/rag_final/model/sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# -----------------------------

def load_faiss_index(index_dir: str):
    index_path = os.path.join(index_dir, "faiss_index.bin")
    meta_path = os.path.join(index_dir, "metadata.pkl")
    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise FileNotFoundError("FAISS index or metadata not found. Build index first.")
    index = faiss.read_index(index_path)
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)
    print("[RAG] Loaded FAISS index and metadata.")
    return index, metadata


class LocalPhi4:
    """Wrapper for local Phi-4-mini-instruct causal LM."""
    def __init__(self, model_path: str, device: str = DEVICE):
        print("[RAG] Loading tokenizer & model from:", model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", local_files_only=True)
        self.device = next(self.model.parameters()).device
        print("[RAG] Model loaded on device:", self.device)

    def generate(self, prompt: str, max_new_tokens: int = 64) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, padding=True).to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        # Remove prompt from output
        return text[len(self.tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)):].strip()


class RAGRunner:
    """Main RAG wrapper to be used in receiver.py"""
    def __init__(self):
        print("[RAG] Initializing RAG runner...")
        # Load embedding model
        self.emb_model = SentenceTransformer(EMBED_MODEL_PATH, device=DEVICE)
        # Load FAISS index and metadata
        self.index, self.metadata = load_faiss_index(INDEX_DIR)
        self.top_k = TOP_K
        # Load local LLM
        self.llm = LocalPhi4(PHI_MODEL_PATH)
        print("[RAG] Ready.")

    def build_prompt_with_context(self, query: str, retrieved_docs: List[Dict], detailed: bool = True):
        ctx_lines = [
            f"Example {i+1}:\nINPUT: {d['input']}\nLABEL: {d.get('output','')}\n"
            for i, d in enumerate(retrieved_docs)
        ]
        context = "\n".join(ctx_lines)

        if detailed:
            prompt = f"""
You are a network flow classifier. Use the following examples as context to classify the input flow.

Context examples:
{context}

Now classify the following input flow. Provide a detailed explanation:
- Compare the input with the context examples
- Explain which features influenced your decision
- Conclude with the final label ('normal' or 'anomaly') at the end

INPUT:
{query}
"""
        else:
            prompt = f"""
You are a network flow classifier. Use the examples in context to classify the input.

Context examples:
{context}

INPUT:
{query}

Return ONLY the label ('normal' or 'anomaly') with no extra text.
"""
        return prompt
