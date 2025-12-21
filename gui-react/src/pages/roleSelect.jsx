import { useState } from "react";

export default function RoleSelect({ onSelect }) {
  const [role, setRole] = useState("sender");

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">Select Role</h1>
      <select
        value={role}
        onChange={(e) => setRole(e.target.value)}
        className="border p-2 mb-4"
      >
        <option value="sender">Sender</option>
        <option value="receiver">Receiver</option>
      </select>
      <button
        onClick={() => onSelect(role)}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Start
      </button>
    </div>
  );
}
