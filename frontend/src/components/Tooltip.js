// src/components/Tooltip.js
import React from "react";

export default function Tooltip({ visible, message, className, onClose }) {
  if (!visible) return null;
  return (
    <div className={`tooltip ${className}`} style={{ marginTop: "1rem", marginBottom: "1rem" }}>
      <span>{message}</span>
      <button onClick={onClose} className="tooltip-close">&times;</button>
    </div>
  );
}
