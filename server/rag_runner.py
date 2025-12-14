import os
import pickle
import faiss
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM

# -----------------------------
INDEX_DIR = "./models/rag_final/faiss_index"
PHI_MODEL_PATH = "./models/rag_final/model/Phi-4-mini-instruct"
EMBED_MODEL_PATH = "./models/rag_final/model/sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# -----------------------------

class LocalPhi4:
    def __init__(self, model_path: str = PHI_MODEL_PATH):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", local_files_only=True)
        self.device = next(self.model.parameters()).device

    def generate(self, prompt: str, max_new_tokens: int = 64) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, padding=True).to(self.device)
        with torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=self.tokenizer.eos_token_id)
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        return text[len(self.tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)):].strip()

class RAGRunner:
    def __init__(self):
        # Load FAISS index + metadata
        index_path = os.path.join(INDEX_DIR, "faiss_index.bin")
        meta_path = os.path.join(INDEX_DIR, "metadata.pkl")
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("FAISS index or metadata not found.")
        self.index = faiss.read_index(index_path)
        print("[RAG] Metadata path:", meta_path)
        print("[RAG] File size:", os.path.getsize(meta_path), "bytes")
        with open(self.meta_path, "rb") as f:
            self.metadata = pickle.load(f)


        # Load embedding model
        self.emb_model = SentenceTransformer(EMBED_MODEL_PATH, device=DEVICE)
        # Load Phi model
        self.llm = LocalPhi4(PHI_MODEL_PATH)

    def generate(self, query: str, detailed: bool = True) -> str:
        # Embed query
        q_emb = self.emb_model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)

        # Search FAISS index
        D, I = self.index.search(q_emb, TOP_K)
        retrieved_docs = [self.metadata[i] for i in I[0].tolist()]

        # Build prompt
        context_lines = [
            f"Example {i+1}:\nINPUT: {d['input']}\nLABEL: {d.get('output','')}\n"
            for i, d in enumerate(retrieved_docs)
        ]
        context = "\n".join(context_lines)

        if detailed:
            prompt = f"""
You are a network flow classifier. Use the following examples as context to classify the input flow.

Context examples:
{context}

Now classify the following input flow. Provide a detailed explanation:
- Compare the input with the context examples
- Explain which features influenced your decision
- Conclude with the final label clearly at the end

INPUT:
{query}
"""
        else:
            prompt = f"""
You are a network flow classifier. Use the context examples to decide if the following flow is "normal" or "anomaly".

Context examples:
{context}

INPUT:
{query}
"""
        # Generate RAG output
        return self.llm.generate(prompt, max_new_tokens=200 if detailed else 32)
