"""
Optimized local RAG runner with Feature Scaling
- Loads embeddings and local Phi-4-mini-instruct
- Loads FAISS index + metadata
- Integrates joblib Scaler to normalize real-time packets
"""

import os
import pickle
import joblib
from typing import List, Dict
import faiss
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM

# -----------------------------
# PATH CONFIGURATION
# -----------------------------
INDEX_DIR = "./models/rag_final/faiss_index"
PHI_MODEL_PATH = "./models/rag_final/model/Phi-4-mini-instruct"
EMBED_MODEL_PATH = "./models/rag_final/model/sentence-transformers/all-MiniLM-L6-v2"
SCALER_PATH = "./models/rag_final/scaler.joblib"  # Path to your saved scaler
TOP_K = 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# The EXACT order of features used during your model training/scaling
FEATURE_COLS = [
    "dur", "sbytes", "dbytes", "Sload", "swin", "stcpb", 
    "smeansz", "Sjit", "Djit", "Stime", "Sintpkt", 
    "tcprtt", "synack", "ct_srv_src", "ct_srv_dst", 
    "ct_dst_ltm", "ct_src_ ltm", "ct_dst_src_ltm"
]

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

    def generate(self, prompt: str, max_new_tokens: int = 512) -> str:
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


class RAGRunner:
    """Main RAG wrapper to be used in receiver.py"""
    def __init__(self):
        print("[RAG] Initializing RAG runner...")
        
        # 1. Load Scaler
        if os.path.exists(SCALER_PATH):
            self.scaler = joblib.load(SCALER_PATH)
            print("[RAG] Scaler loaded.")
        else:
            print(f"[WARNING] Scaler not found at {SCALER_PATH}. Using raw features.")
            self.scaler = None

        # 2. Load embedding model
        self.emb_model = SentenceTransformer(EMBED_MODEL_PATH, device=DEVICE)
        
        # 3. Load FAISS index and metadata
        self.index, self.metadata = load_faiss_index(INDEX_DIR)
        self.top_k = TOP_K
        
        # 4. Load local LLM
        self.llm = LocalPhi4(PHI_MODEL_PATH)
        print("[RAG] Ready.")

    def get_scaled_query_str(self, raw_data_dict: Dict) -> str:
        """Helper to transform raw dictionary to scaled feature string."""
        if not self.scaler:
            return str(raw_data_dict)
            
        # Extract values in correct order for scaler
        vals = [raw_data_dict.get(col, 0) for col in FEATURE_COLS]
        # Scale values
        scaled_vals = self.scaler.transform([vals])[0]
        # Format string (matches metadata context)
        return " | ".join([f"{col}: {round(val, 4)}" for col, val in zip(FEATURE_COLS, scaled_vals)])

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
- dont say you dont have no information about any thing 
- give the answer like you are networking instructor
- but dont deiny with any prediction wich is given to you
- give professional and well thought answers

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