import React, { useState, useEffect } from "react";
import axios from "axios";

const SENDER_API = "http://localhost:9001";

export default function Sender() {
  const [isRunning, setIsRunning] = useState(false);
  const [statusMessage, setStatusMessage] = useState("SYSTEM_IDLE");
  
  // State for the SenderConfig required by your FastAPI backend
  const [config, setConfig] = useState({
    host: "127.0.0.1",
    port: 9999,
    delay: 0.5
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: name === "host" ? value : parseFloat(value) || 0
    }));
  };

  const startSender = async () => {
    try {
      setStatusMessage("INITIALIZING_UPLINK...");
      // Sending the config object required by your Pydantic model
      const res = await axios.post(`${SENDER_API}/start`, config);
      if (res.status === 200) {
        setIsRunning(true);
        setStatusMessage("TRANSMISSION_ACTIVE");
      }
    } catch (err) {
      console.error(err);
      setStatusMessage("CONFIG_OR_CONNECTION_ERROR");
    }
  };

  const stopSender = async () => {
    try {
      const res = await axios.post(`${SENDER_API}/stop`);
      if (res.status === 200) {
        setIsRunning(false);
        setStatusMessage("TRANSMISSION_HALTED");
      }
    } catch (err) {
      console.error(err);
      setStatusMessage("TERMINATION_FAILURE");
    }
  };

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${SENDER_API}/status`);
        setIsRunning(res.data.running);
      } catch (err) {
        // Silent fail on polling to keep UI clean
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-[#050E3C] min-h-screen p-8 text-white font-sans relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-[#DC0000] rounded-full blur-[150px] opacity-10 animate-pulse" />

      <div className="max-w-4xl mx-auto relative z-10">
        <header className="bg-[#002455]/40 backdrop-blur-xl border border-white/10 p-10 rounded-[2.5rem] shadow-2xl mb-10 text-center">
          <h1 className="text-5xl font-black tracking-[-0.05em] text-white">
            COMMAND <span className="text-[#DC0000]">UPLINK</span>
          </h1>
          <p className="text-[#FF3838] text-xs mt-3 uppercase tracking-[0.6em] font-bold opacity-80">
            UDP Packet Injection Hub
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {/* Host Input */}
          <div className="bg-[#002455]/30 backdrop-blur-md border border-white/10 p-6 rounded-3xl">
            <label className="block text-[10px] font-black text-[#FF3838] mb-2 tracking-widest">TARGET_HOST</label>
            <input 
              name="host" value={config.host} onChange={handleInputChange}
              className="bg-black/40 border border-white/5 w-full p-3 rounded-xl text-sm font-mono focus:outline-none focus:border-[#DC0000] transition-colors"
            />
          </div>
          {/* Port Input */}
          <div className="bg-[#002455]/30 backdrop-blur-md border border-white/10 p-6 rounded-3xl">
            <label className="block text-[10px] font-black text-[#FF3838] mb-2 tracking-widest">TARGET_PORT</label>
            <input 
              name="port" type="number" value={config.port} onChange={handleInputChange}
              className="bg-black/40 border border-white/5 w-full p-3 rounded-xl text-sm font-mono focus:outline-none focus:border-[#DC0000] transition-colors"
            />
          </div>
          {/* Delay Input */}
          <div className="bg-[#002455]/30 backdrop-blur-md border border-white/10 p-6 rounded-3xl">
            <label className="block text-[10px] font-black text-[#FF3838] mb-2 tracking-widest">BURST_DELAY (S)</label>
            <input 
              name="delay" type="number" step="0.1" value={config.delay} onChange={handleInputChange}
              className="bg-black/40 border border-white/5 w-full p-3 rounded-xl text-sm font-mono focus:outline-none focus:border-[#DC0000] transition-colors"
            />
          </div>
        </div>

        <div className="bg-[#002455]/20 backdrop-blur-lg border border-white/10 p-12 rounded-[3rem] text-center relative">
          <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-32 h-1 rounded-b-full ${isRunning ? "bg-[#DC0000] shadow-[0_0_15px_#DC0000]" : "bg-white/10"}`} />
          
          <div className="mb-10">
            <p className="text-gray-500 text-[10px] font-black tracking-[0.4em] mb-2">SYSTEM_LOG</p>
            <div className={`text-xl font-mono font-bold ${isRunning ? "text-[#FF3838]" : "text-white/30"}`}>
              {statusMessage}
            </div>
          </div>

          <div className="flex gap-6">
            <button
              onClick={startSender} disabled={isRunning}
              className={`flex-1 py-5 rounded-2xl font-black text-xs tracking-[0.3em] border-2 transition-all duration-500 ${
                isRunning ? "border-gray-800 text-gray-700" : "bg-[#DC0000] border-[#DC0000] hover:bg-transparent hover:text-[#DC0000]"
              }`}
            >
              [ ENGAGE_UPLINK ]
            </button>
            <button
              onClick={stopSender} disabled={!isRunning}
              className={`flex-1 py-5 rounded-2xl font-black text-xs tracking-[0.3em] border-2 transition-all duration-500 ${
                !isRunning ? "border-gray-800 text-gray-700" : "border-white/20 hover:bg-white hover:text-black"
              }`}
            >
              [ CEASE_FIRE ]
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}