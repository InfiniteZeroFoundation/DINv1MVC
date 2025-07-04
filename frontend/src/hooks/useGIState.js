// src/hooks/useGIState.js
import { useState, useEffect } from "react";

export default function useGIState(showTooltip, activeTab) {
  const [GI, setGI] = useState(0);
  const [GIstate, setGIstate] = useState(0);
  const [GIstatedes, setGIstatedes] = useState("AwaitingGenesisModel");
  const [loading, setLoading] = useState(true);

  const fetchGIState = async () => {
    try {
      const response = await fetch("http://localhost:8000/getGIState");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setGI(data.GI);
      setGIstate(data.GIstate);
      setGIstatedes(data.GIstatedes);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching GI state:", err);
      showTooltip(err.message, true);
    }
  };

  useEffect(() => {
    fetchGIState();
  }, [activeTab]);

  return {
    GI,
    GIstate,
    GIstatedes,
    loading,
    setGI,
    setGIstate,
    setGIstatedes,
    fetchGIState
  };
}
