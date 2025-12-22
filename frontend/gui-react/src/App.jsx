import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Receiver from "./pages/receiver";
import Sender from "./pages/sender";

export default function App() {
  return (
    <BrowserRouter>
      <div className="bg-[#050E3C] min-h-screen font-sans selection:bg-[#DC0000]/30">
        
        {/* Minimalist Top Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-[100] flex justify-center p-6 pointer-events-none">
          <div className="pointer-events-auto bg-[#002455]/40 backdrop-blur-md border border-white/5 px-2 py-1.5 rounded-full flex gap-1 shadow-2xl">
            <NavLink 
              to="/sender" 
              className={({ isActive }) => `px-6 py-2 rounded-full text-[10px] font-black tracking-[0.2em] transition-all duration-300 ${
                isActive ? "bg-[#DC0000] text-white shadow-[0_0_15px_rgba(220,0,0,0.3)]" : "text-gray-400 hover:text-white"
              }`}
            >
              UPLINK
            </NavLink>
            <NavLink 
              to="/receiver" 
              className={({ isActive }) => `px-6 py-2 rounded-full text-[10px] font-black tracking-[0.2em] transition-all duration-300 ${
                isActive ? "bg-[#DC0000] text-white shadow-[0_0_15px_rgba(220,0,0,0.3)]" : "text-gray-400 hover:text-white"
              }`}
            >
              SENTINEL
            </NavLink>
          </div>
        </nav>

        {/* Page Content */}
        <div className="pt-20"> {/* Padding top to clear the fixed nav */}
          <Routes>
            <Route path="/" element={<Receiver />} />
            <Route path="/sender" element={<Sender />} />
            <Route path="/receiver" element={<Receiver />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}