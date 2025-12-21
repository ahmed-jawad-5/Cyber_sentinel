Cyber Sentinel
Project Overview

Cyber Sentinel is a real-time network traffic monitoring and analysis system that leverages machine learning (XGBoost) and retrieval-augmented generation (RAG) for anomaly detection. It captures network flows from a sender, sends them to a receiver, predicts their labels, and provides detailed AI-assisted explanations for anomalies.

Key Features

Real-time Packet Capture & Transmission

Captures network flows using a feature extractor.

Sender sends extracted features over TCP to a receiver.

Receiver collects the packets, stores them, and runs predictions.

Machine Learning Integration

Uses XGBoost for multi-class classification of network flows.

Predicts packet labels such as normal, backdoor, dos, etc.

Tracks prediction probabilities for more granular analysis.

RAG-based Anomaly Analysis

Implements a local RAG pipeline to generate AI explanations for anomalies.

Provides detailed reasoning comparing anomalous flows with historical examples.

RAG is triggered only for the first few detected anomalies to optimize performance.

Persistent Storage

Features and predictions are stored in a CSV file for audit and analysis.

CSV columns include packet features, prediction label, reconstruction error, and RAG output.

Custom DB Using Data Structures

Linked List: Stores rows efficiently with O(1) insertion and deletion.

Hash Table: Ensures primary key uniqueness and fast equality-based lookups.

Dictionary (RID to Node): Maps Record IDs to linked list nodes for fast access.

B+ Tree: Enables efficient sorted queries and range searches.

Cross-Platform GUI

Built using Electron.js for a modern, responsive desktop application.

Users can select Sender or Receiver mode.

Live tables display packet number, source IP, prediction, and anomaly details.

"Show Details" button reveals all features of a packet.

"AI Suggestion" button runs RAG on anomalies and shows results to the user.

Workflow
1. Sender

Captures network flows from the local machine.

Extracts 18 features per flow (e.g., duration, byte counts, timestamps).

Sends feature dictionaries over TCP to the receiver.

Supports configurable packet sending intervals (e.g., 5 seconds gap between packets).

2. Receiver

Listens on a configurable port for incoming TCP connections.

Validates feature count per packet.

Stores features in CSV along with prediction placeholders.

Runs XGBoost predictions and updates CSV with results.

Triggers RAG for first 3 anomalous packets to provide detailed AI feedback.

3. Data Management

CSV files track all packet features, predictions, and RAG outputs.

Primary keys are auto-generated if missing.

Custom DB data structures (linked list, hash table, dictionary, B+ tree) optimize insertion, deletion, retrieval, and range queries.

4. GUI Integration

Electron.js provides a cross-platform desktop interface.

Sender inputs receiver IP and packet count.

Receiver displays live packet counts, predictions, and detailed analysis.

Anomaly packets can trigger AI suggestions via RAG.

Technical Stack

Python 3.11 (backend: packet capture, ML, RAG)

TCP Sockets for real-time communication

XGBoost for multi-class classification

RAG Pipeline:

Sentence-Transformers for embeddings

FAISS for fast similarity search

Phi-4-mini-instruct for local text generation

Custom DB Using Data Structures: Linked List, Hash Table, Dictionary, B+ Tree

CSV Storage for persistent packet logging

Electron.js GUI for interactive desktop interface

Example Flow
```
Sender extracts features:

{
  "dur": 0.001,
  "sbytes": 94,
  "dbytes": 0,
  "Sload": 11.45,
  ...
  "ct_dst_src_ltm": 1
}
```
```
Receiver predicts label:

{
  "prediction": 0.42,
  "label": "backdoor"
}
```

If anomaly, RAG generates reasoning:

Input flow matches historical backdoor patterns:
- High Sload
- Low Dbytes
- Anomaly detected in stcpb sequence
Suggested label: backdoor


CSV is updated:
```
| dur | sbytes | dbytes | ... | prediction | label | rag_output |
|-----|-------|-------|-----|------------|-------|------------|
| 0.001 | 94 | 0 | ... | 0.42 | backdoor | Generated reasoning text |
```
Notes

Ensure server binds to 0.0.0.0 for LAN access.

Open TCP port (default 9000) in firewall for connectivity.

RAG is computationally expensive; only triggered for first few anomalies to maintain performance.

Electron.js GUI can be packaged for Windows, Linux, and macOS for cross-platform usage.
