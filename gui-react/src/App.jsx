import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000";

export default function App() {
  const [receiverRunning, setReceiverRunning] = useState(false);
  const [alerts, setAlerts] = useState([]);

  const fetchAlerts = async () => {
    try {
      const res = await axios.get(`${API_URL}/alerts`);
      setAlerts((prevAlerts) => {
        const newAlerts = res.data.alerts || [];
        return newAlerts.map((newA) => {
          const existing = prevAlerts.find((p) => p.flow.id === newA.flow.id);
          return existing ? { ...newA, rag_prompt: existing.rag_prompt } : newA;
        });
      });
    } catch (err) {
      console.error("Error fetching alerts:", err);
    }
  };

  const checkStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/status`);
      setReceiverRunning(res.data.receiver_running);
    } catch (err) {
      console.error("Status check failed:", err);
    }
  };

  const startCapture = async () => {
    try {
      await axios.post(`${API_URL}/start`);
      setReceiverRunning(true);
    } catch (err) {
      console.error("Start capture failed:", err);
    }
  };

  const fetchRag = async (packetId) => {
    try {
      setAlerts((prev) =>
        prev.map((a) =>
          a.flow.id === packetId ? { ...a, rag_prompt: "📡 RUNNING HEURISTIC ANALYSIS..." } : a
        )
      );
      const res = await axios.post(`${API_URL}/explain/${packetId}`);
      const explanation = res.data.explanation;
      setAlerts((prev) =>
        prev.map((a) =>
          a.flow.id === packetId ? { ...a, rag_prompt: explanation } : a
        )
      );
    } catch (err) {
      console.error("RAG error:", err);
      setAlerts((prev) =>
        prev.map((a) =>
          a.flow.id === packetId ? { ...a, rag_prompt: "⚠️ ANALYSIS FAILED." } : a
        )
      );
    }
  };

  useEffect(() => {
    checkStatus();
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-[#050E3C] min-h-screen p-8 text-white font-sans">
      <div className="max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row justify-between items-center mb-12 gap-6 border-b border-[#002455] pb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tighter text-white">
              CYBER <span className="text-[#DC0000]">SENTINEL</span>
            </h1>
            <p className="text-[#FF3838] text-[10px] mt-1 uppercase tracking-[0.4em] font-bold">
              Packet Analysis AI
            </p>
          </div>

          <button
            onClick={startCapture}
            disabled={receiverRunning}
            className={`px-10 py-3 rounded-md font-black text-xs transition-all duration-300 tracking-widest border-2 ${
              receiverRunning
                ? "bg-transparent text-gray-500 border-gray-700 cursor-not-allowed"
                : "bg-[#DC0000] hover:bg-[#FF3838] text-white border-[#DC0000] hover:shadow-[0_0_20px_rgba(220,0,0,0.4)] active:scale-95"
            }`}
          >
            {receiverRunning ? "SYSTEM LIVE" : "INITIALIZE SCAN"}
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {alerts.length === 0 ? (
            <div className="col-span-full py-32 text-center border-2 border-[#002455] rounded-lg bg-[#002455]/20">
              <p className="text-gray-500 text-sm font-bold uppercase tracking-widest animate-pulse">
                {receiverRunning ? "Scanning Network Buffers..." : "System Idle"}
              </p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.flow.id}
                className="group relative bg-[#002455] border-l-4 border-[#DC0000] p-6 rounded-r-lg shadow-2xl transition-all hover:translate-y-[-4px]"
              >
                <div className="flex justify-between items-center mb-6">
                  <span className={`px-3 py-1 text-[10px] font-bold tracking-widest rounded ${
                    alert.flow.label?.toLowerCase() === "normal" 
                    ? "bg-white/10 text-white" 
                    : "bg-[#DC0000] text-white"
                  }`}>
                    {alert.flow.label?.toUpperCase() || "DATA"}
                  </span>
                  
                  <button
                    onClick={() => fetchRag(alert.flow.id)}
                    className="text-[#FF3838] hover:text-white text-[10px] font-black uppercase tracking-tighter transition-colors"
                  >
                    [ Analyze ]
                  </button>
                </div>

                <div className="space-y-3 mb-6">
                  <div className="flex justify-between">
                    <span className="text-gray-400 text-[9px] uppercase font-bold">Origin_IP</span>
                    <span className="font-mono text-xs text-white">{alert.flow.srcip}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 text-[9px] uppercase font-bold">Risk_Factor</span>
                    <span className={`font-mono text-xs font-bold ${
                      alert.flow.reconstruction_error > 0.4 ? "text-[#FF3838]" : "text-white"
                    }`}>
                      {(alert.flow.reconstruction_error * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>

                <div className="bg-[#050E3C] rounded p-4 mb-6 border border-white/5">
                  <pre className="text-[10px] text-gray-400 font-mono h-24 overflow-y-auto custom-scrollbar">
                    {JSON.stringify(alert.flow, null, 2)}
                  </pre>
                </div>

                <div className="bg-black/20 p-4 border-t border-[#DC0000]/30">
                  <h4 className="text-[9px] font-black text-[#FF3838] uppercase mb-2 tracking-widest">
                    AI_INTERPRETATION
                  </h4>
                  <p className="text-[11px] text-gray-200 leading-relaxed font-medium">
                    {alert.rag_prompt || "Awaiting Manual Trigger..."}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #050E3C; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #DC0000; }
      `}</style>
    </div>
  );
}