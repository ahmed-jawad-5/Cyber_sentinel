"""
Optimized local RAG pipeline:
- Embedding model loaded once
- FAISS index built only if missing
- Uses local Phi-4-mini-instruct for generation
"""

import os
import json
import pickle
from typing import List, Dict
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# -----------------------------
TRAIN_FILE = "data/unsw_llm_dataset_train.jsonl"
INDEX_DIR = "faiss_index"
PHI_MODEL_PATH = "./model/Phi-4-mini-instruct"
EMBED_MODEL_PATH = "./model/sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# -----------------------------

os.makedirs(INDEX_DIR, exist_ok=True)


def load_jsonl(path: str) -> List[Dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def build_embeddings(texts: List[str], model_path: str):
    print("Loading embedding model:", model_path)
    emb_model = SentenceTransformer(model_path, device=DEVICE)
    print("Encoding texts to embeddings...")
    embeddings = emb_model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    faiss.normalize_L2(embeddings)
    return embeddings, emb_model


def build_faiss_index(embeddings: np.ndarray, index_dir: str):
    d = embeddings.shape[1]
    print(f"Building FAISS Index (dim={d}) ...")
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    index_path = os.path.join(index_dir, "faiss_index.bin")
    faiss.write_index(index, index_path)
    print("Saved FAISS index to:", index_path)
    return index_path


def save_metadata(metadata: List[Dict], index_dir: str):
    meta_path = os.path.join(index_dir, "metadata.pkl")
    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)
    print("Saved metadata to:", meta_path)
    return meta_path


def load_faiss_index(index_dir: str):
    index_path = os.path.join(index_dir, "faiss_index.bin")
    meta_path = os.path.join(index_dir, "metadata.pkl")
    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise FileNotFoundError("FAISS index or metadata not found. Build index first.")
    index = faiss.read_index(index_path)
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)
    print("Loaded FAISS index and metadata.")
    return index, metadata


class LocalPhi4:
    """Wrapper for local Phi-4-mini-instruct causal LM."""
    def __init__(self, model_path: str, device: str = DEVICE):
        print("Loading tokenizer & model from:", model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", local_files_only=True)
        self.device = next(self.model.parameters()).device
        print("Model loaded on device:", self.device)

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
        return text[len(self.tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)):].strip()


def build_prompt_with_context(query: str, retrieved_docs: List[Dict], detailed: bool = False):
    """
    Build a prompt for the LLM.
    If detailed=True, asks the model to provide a full reasoning with comparison to examples.
    """
    ctx_lines = [
        f"Example {i+1}:\nINPUT: {d['input']}\nLABEL: {d.get('output','')}\n"
        for i, d in enumerate(retrieved_docs)
    ]
    context = "\n".join(ctx_lines)

    if detailed:
        # Prompt for detailed explanation
        prompt = f"""
    You are a network flow classifier. Use the following examples as context to classify the input flow.

    Context examples:
    {context}

    Now classify the following input flow. Provide a **detailed explanation**:
    - Compare the input with the context examples
    - Explain which features (dur, sbytes, dbytes, Sload, etc.) influenced your decision
    - Conclude with the final label ('normal' or 'anomaly') clearly at the end

    INPUT:
    {query}
    """
        else:
            # Original concise prompt
            prompt = f"""
    You are a network flow classifier. Use the examples in context to decide if the following flow is "normal" or "anomaly".

    Context examples:
    {context}

    Now classify this input. Return ONLY the label ('normal' or 'anomaly') with no extra text.

    INPUT:
    {query}
    """
        return prompt


def index_exists(index_dir: str) -> bool:
    return os.path.exists(os.path.join(index_dir, "faiss_index.bin")) and \
           os.path.exists(os.path.join(index_dir, "metadata.pkl"))


def test_rag_pipeline(detailed: bool = True):
    print("\n🔍 TESTING RAG PIPELINE\n")

    # Load index + metadata
    index, metadata = load_faiss_index(INDEX_DIR)

    # Load embedding model
    emb_model = SentenceTransformer(EMBED_MODEL_PATH, device=DEVICE)

    # Load Phi model
    llm = LocalPhi4(PHI_MODEL_PATH)

    # ----------------------------
    # 1. Test query
    # ----------------------------
    query = "dur: 0.4 | sbytes: -0.8 | dbytes: 1.1 | sload: -1.0"
    print("\n📌 TEST QUERY:", query)

    # ----------------------------
    # 2. Embed query
    # ----------------------------
    q_emb = emb_model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)

    # ----------------------------
    # 3. Search FAISS index
    # ----------------------------
    D, I = index.search(q_emb, TOP_K)
    retrieved_docs = [metadata[i] for i in I[0].tolist()]

    # ----------------------------
    # 4. Build prompt
    # ----------------------------
    prompt = build_prompt_with_context(query, retrieved_docs, detailed=detailed)

    # ----------------------------
    # 5. Generate detailed output
    # ----------------------------
    max_tokens = 200 if detailed else 32  # allow longer output for detailed reasoning
    result = llm.generate(prompt, max_new_tokens=max_tokens)

    # ----------------------------
    # 6. Print retrieved examples
    # ----------------------------
    print("\n📚 Retrieved examples:")
    for j, doc in enumerate(retrieved_docs):
        print(f"\n--- Example {j+1} ---")
        print("INPUT :", doc['input'])
        print("LABEL :", doc.get('output', '?'))

    # ----------------------------
    # 7. Print full LLM output
    # ----------------------------
    if detailed:
        print("\n🤖 DETAILED MODEL OUTPUT:\n")
    else:
        print("\n🤖 MODEL OUTPUT:")
    print(result)
    print("\n🎉 RAG TEST COMPLETE!\n")


if __name__ == "__main__":
    # Run test in detailed mode
    test_rag_pipeline(detailed=True)
