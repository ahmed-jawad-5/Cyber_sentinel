import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000";

export default function Receiver() {
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
          a.flow.id === packetId ? { ...a, rag_prompt: "⚡ INITIATING ROYAL DECREE (AI ANALYSIS)..." } : a
        )
      );
      const res = await axios.post(`${API_URL}/explain/${packetId}`);
      setAlerts((prev) =>
        prev.map((a) =>
          a.flow.id === packetId ? { ...a, rag_prompt: res.data.explanation } : a
        )
      );
    } catch (err) {
      console.error("RAG error:", err);
      setAlerts((prev) =>
        prev.map((a) =>
          a.flow.id === packetId ? { ...a, rag_prompt: "⚠️ COMMAND FAILED." } : a
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
    <div className="bg-[#050E3C] min-h-screen p-8 text-white font-sans relative overflow-hidden">
      {/* Background radial glows for depth */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-[#DC0000] rounded-full blur-[150px] opacity-10" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-[#002455] rounded-full blur-[150px] opacity-50" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Glass Header */}
        <header className="flex flex-col md:flex-row justify-between items-center mb-16 gap-6 bg-[#002455]/40 backdrop-blur-xl border border-white/10 p-10 rounded-[2rem] shadow-2xl">
          <div className="text-center md:text-left">
            <h1 className="text-5xl font-black tracking-[-0.05em] text-white">
              CYBER <span className="text-[#DC0000]">SENTINEL</span>
            </h1>
            <p className="text-[#FF3838] text-xs mt-2 uppercase tracking-[0.6em] font-bold opacity-80">
              Sovereign Packet Intelligence
            </p>
          </div>

          <button
            onClick={startCapture}
            disabled={receiverRunning}
            className={`px-12 py-4 rounded-full font-black text-xs transition-all duration-500 tracking-[0.2em] border-2 shadow-2xl ${
              receiverRunning
                ? "bg-transparent text-gray-500 border-gray-700 cursor-not-allowed"
                : "bg-[#DC0000] hover:bg-transparent hover:text-[#DC0000] text-white border-[#DC0000] hover:shadow-[0_0_30px_rgba(220,0,0,0.5)] active:scale-95"
            }`}
          >
            {receiverRunning ? "SYSTEM ONLINE" : "ENGAGE COMMAND"}
          </button>
        </header>

        {/* Monarch Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
          {alerts.length === 0 ? (
            <div className="col-span-full py-40 text-center bg-white/5 backdrop-blur-sm border-2 border-dashed border-[#002455] rounded-[3rem]">
              <p className="text-gray-400 text-sm font-bold uppercase tracking-[0.3em] animate-pulse">
                {receiverRunning ? "Listening for Network Vassals..." : "Sovereign Disconnected"}
              </p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.flow.id}
                className="group relative bg-[#002455]/30 backdrop-blur-lg border border-white/10 p-8 rounded-[2.5rem] shadow-2xl transition-all duration-500 hover:scale-[1.02] hover:bg-[#002455]/50 hover:border-[#DC0000]/50"
              >
                {/* Visual "Crown" status indicator */}
                <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-24 h-1.5 rounded-b-full shadow-lg ${
                    alert.flow.label?.toLowerCase() === "normal" ? "bg-white/20" : "bg-[#DC0000]"
                }`} />

                <div className="flex justify-between items-center mb-10">
                  <span className={`px-4 py-1 text-[9px] font-black tracking-widest rounded-full border ${
                    alert.flow.label?.toLowerCase() === "normal" 
                    ? "bg-white/5 text-white border-white/20" 
                    : "bg-[#DC0000]/20 text-[#FF3838] border-[#DC0000]/50"
                  }`}>
                    {alert.flow.label?.toUpperCase() || "LOG"}
                  </span>
                  
                  <button
                    onClick={() => fetchRag(alert.flow.id)}
                    className="text-[#FF3838] hover:text-white text-[10px] font-black uppercase tracking-widest transition-all hover:drop-shadow-[0_0_10px_#FF3838]"
                  >
                    [ EXECUTE ANALYSIS ]
                  </button>
                </div>

                <div className="space-y-4 mb-8">
                  <div className="flex justify-between items-center bg-black/20 p-3 rounded-xl border border-white/5">
                    <span className="text-gray-500 text-[9px] uppercase font-black tracking-tighter">Vassal_IP</span>
                    <span className="font-mono text-xs text-white">{alert.flow.srcip}</span>
                  </div>
                  <div className="flex justify-between items-center bg-black/20 p-3 rounded-xl border border-white/5">
                    <span className="text-gray-500 text-[9px] uppercase font-black tracking-tighter">Threat_Index</span>
                    <span className={`font-mono text-sm font-black ${
                      alert.flow.reconstruction_error > 0.4 ? "text-[#FF3838]" : "text-white"
                    }`}>
                      {(alert.flow.reconstruction_error * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>

                {/* Glassy Code View */}
                <div className="bg-black/40 rounded-2xl p-5 mb-8 border border-white/5 shadow-inner">
                  <pre className="text-[10px] text-gray-400 font-mono h-28 overflow-y-auto custom-scrollbar italic leading-relaxed">
                    {JSON.stringify(alert.flow, null, 2)}
                  </pre>
                </div>

                {/* AI Interpretation (The Royal Decree) */}
                <div className="bg-[#DC0000]/5 backdrop-blur-2xl p-6 rounded-[1.5rem] border border-[#DC0000]/20 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1.5 h-full bg-[#DC0000]" />
                  <h4 className="text-[10px] font-black text-[#FF3838] uppercase mb-3 tracking-[0.2em] flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-[#DC0000] rounded-full animate-pulse" />
                    AI_DECREE
                  </h4>
                  <p className="text-[12px] text-gray-200 leading-relaxed font-medium">
                    {alert.rag_prompt || "Standing by for Sovereign Command..."}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}