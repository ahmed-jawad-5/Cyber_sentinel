import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000";

export default function App() {
  const [receiverRunning, setReceiverRunning] = useState(false);
  const [alerts, setAlerts] = useState([]);

  const checkStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/status`);
      setReceiverRunning(res.data.receiver_running);
    } catch (err) {
      console.error(err);
    }
  };

  const startCapture = async () => {
    try {
      await axios.post(`${API_URL}/start`);
      checkStatus();
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await axios.get(`${API_URL}/alerts`);
      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    checkStatus();
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 min-h-screen p-8 text-white font-sans">
      <h1 className="text-4xl font-extrabold mb-6 text-center text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-purple-500 animate-pulse">
        🚀 Network Anomaly Dashboard
      </h1>

      <div className="flex justify-center mb-8">
        <button
          onClick={startCapture}
          disabled={receiverRunning}
          className={`px-6 py-3 rounded-lg text-lg font-semibold transition-all duration-300 shadow-lg ${
            receiverRunning
              ? "bg-gray-700 cursor-not-allowed"
              : "bg-gradient-to-r from-green-400 to-blue-500 hover:scale-105 hover:from-green-500 hover:to-blue-600"
          }`}
        >
          {receiverRunning ? "Receiver Running" : "Start Capture"}
        </button>
      </div>

      <h2 className="text-3xl font-bold mb-4 text-pink-400">Recent Alerts</h2>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {alerts.length === 0 && (
          <p className="text-gray-400 text-center col-span-full">
            No anomalies detected yet.
          </p>
        )}
        {alerts.map((alert, idx) => (
          <div
            key={idx}
            className="bg-gray-800 p-4 rounded-xl shadow-2xl border border-purple-600 transform hover:scale-105 transition-transform duration-300"
          >
            <div className="mb-2 flex justify-between items-center">
              <span className="font-bold text-lg text-red-400">
                Label: {alert.flow?.label || "N/A"}
              </span>
              <span className="text-sm text-green-400">
                Error: {alert.flow?.reconstruction_error || "N/A"}
              </span>
            </div>

            <div className="mb-2">
              <span className="font-semibold text-blue-400">Flow Details:</span>
              <pre className="bg-gray-900 text-sm p-2 mt-1 rounded overflow-x-auto">
                {JSON.stringify(alert.flow, null, 2)}
              </pre>
            </div>

            <div>
              <span className="font-semibold text-yellow-400">RAG Explanation:</span>
              <p className="text-sm mt-1 text-gray-200">{alert.rag_prompt || "No explanation available."}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
