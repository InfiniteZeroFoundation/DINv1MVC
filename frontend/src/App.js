import logo from './logo.svg';
import './App.css';
import React, { useState, useEffect, useContext } from "react";
import { TooltipProvider, TooltipContext } from "./context/TooltipContext"; 
import Tooltip from "./components/Tooltip";
import DINDAOTab from "./tabs/DINDAOTab";
import ModelOwnerTab from "./tabs/ModelOwnerTab";
import ClientsTab from "./tabs/ClientsTab";
import ValidatorsTab from "./tabs/ValidatorsTab";

/** ======================= TAB BAR ======================= */
function TabBar({ activeTab, setActiveTab }) {
  // We include a 'validator' tab
  const tabs = ["DINDAO", "ModelOwner", "Validators", "Clients" ];
  return (
    <div className="tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={activeTab === tab ? "tab-button active" : "tab-button"}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState("DINDAO");
  const { tooltipVisible, tooltipMsg, tooltipClass, hideTooltip, showTooltip } = useContext(TooltipContext);
  const [GI,setGI] = useState(0);
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
      console.log(data);
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


  const handleResetAll = async () => {
    try {
      const response = await fetch("http://localhost:8000/reset/resetall");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.message);

      // Show tooltip
      if (data.status === "success") {
        showTooltip(data.message, false);
      } else {
        showTooltip(data.message, true);
      }

      // Reload the page after 1 second
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (err) {
      console.error("Error resetting all:", err);
      // Show error tooltip
      showTooltip(err.message, true);
    }
  };

  const handleDistributeDataset = async () => {
    try {
      const response = await fetch("http://localhost:8000/distribute/dataset");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.message);

      // Show tooltip
      if (data.status === "success") {
        showTooltip(data.message, false);
      } else {
        showTooltip(data.message, true);
      }
    } catch (err) {
      console.error("Error distributing dataset:", err);
      // Show error tooltip
      showTooltip(err.message, true);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>DIN MVP</h1>
        <nav className="navbar">
          <ul>
            {/* Add external links if desired */}
            <li>
              <a href="https://github.com/">GitHub</a>
            </li>
            <li>
              <a href="https://github.com/Doctelligence/DINv1MVC/blob/master/Documentation.md">Documentation</a>
            </li>
          </ul>
        </nav>
      </header>
      <Tooltip
        visible={tooltipVisible}
        message={tooltipMsg}
        className={tooltipClass}
        onClose={hideTooltip}
      />
      <main className="main-content">
        <div className="container" style={{ marginTop: "1rem", marginBottom: "1rem" }}>
          <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
            <button className="button button--danger" onClick={handleResetAll}>
              Reset All
            </button>
            <button
              className="button button--primary" 
              style={{ marginLeft: "1rem" }} 
              onClick={handleDistributeDataset}
            >
              Distribute Dataset
            </button>
          </div>

          {loading ? (
            <div>Loading...</div>
          ) : (
            <>
            <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
              <h3>Global Iteration: {GI}</h3>
              <h3>Global Iteration State: {GIstatedes}</h3>
            </div>
            </>
          )}
            
          <TabBar activeTab={activeTab} setActiveTab={setActiveTab} />
          {activeTab === "DINDAO" && <DINDAOTab />}
          {activeTab === "ModelOwner" && <ModelOwnerTab setGIstate={setGIstate} fetchGIState={fetchGIState} GIstate={GIstate} GIstatedes={GIstatedes} setGIstatedes={setGIstatedes}/>}
          {activeTab === "Validators" && <ValidatorsTab GIstate={GIstate} GI={GI} setGIstatedes={setGIstatedes}/>}
          {activeTab === "Clients" && <ClientsTab setGIstate={setGIstate} fetchGIState={fetchGIState} GIstate={GIstate} GIstatedes={GIstatedes} setGIstatedes={setGIstatedes}/>}
        </div>
      </main>

      <footer className="footer">
        <p>&copy; 2025 DIN MVP</p>
      </footer>
    </div>
  );
}

export default App;
