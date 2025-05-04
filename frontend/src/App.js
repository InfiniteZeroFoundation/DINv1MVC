import logo from './logo.svg';
import './App.css';
import React, { useState, useEffect, useContext } from "react";
import { TooltipProvider, TooltipContext } from "./context/TooltipContext"; 


/** ======================= TAB BAR ======================= */
function TabBar({ activeTab, setActiveTab }) {
  // We include a 'validator' tab
  const tabs = ["ModelOwner", "Clients", "Validators"];
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

/** ======================= ModelOwner TAB ======================= */
function ModelOwnerTab() {
  const [genesisModelsetF, setGenesisModelF] = useState(false);
  const { showTooltip } = useContext(TooltipContext);
  const [dincordinator_address, setDincoordinatorAddress] = useState(null);
  const [genesis_model_ipfs_hash, setGenesisModelIpfsHash] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch the initial state of genesisModelF from the FastAPI backend
  useEffect(() => {
    const fetchGenesisModelState = async () => {
      try {
        const response = await fetch("http://localhost:8000/modelowner/getGenesisModelsetF", { method: "POST" });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Initial genesisModelF state:", data.IS_GenesisModelCreated);
        console.log(data);
        // Update the state based on the server response
        setGenesisModelF(data.IS_GenesisModelCreated);
        setDincoordinatorAddress(data.dincordinator_address);
        setGenesisModelIpfsHash(data.model_ipfs_hash);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching genesisModelF state:", err);
        // Optionally show an error tooltip
        showTooltip(err.message, true);
      }
    };

    fetchGenesisModelState(); // Call the function when the component mounts
  },[]); // Add dependencies if necessary (e.g., showTooltip)


  
  const createGenesisModel = async () => {
    try {
      const response = await fetch("http://localhost:8000/modelowner/createGenesisModel", { method: "POST" }); // Assuming this is a POST request
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.message);
      
      // Show tooltip
      if (data.status === "success") {
        setGenesisModelF(data.IS_GenesisModelCreated);
        setDincoordinatorAddress(data.dincordinator_address);
        setGenesisModelIpfsHash(data.model_ipfs_hash);
        showTooltip(data.message, false);
      } else {
        showTooltip(data.message, true);
      }
    } catch (err) {
      console.error("Error creating genesis model:", err);
      // Show error tooltip
      showTooltip(err.message, true);
    }
  };
  
  return (
    <div className="tab-content">
      <h2>ModelOwner</h2>
      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
        {genesisModelsetF ? (
          <div>
            <h3>Genesis Model Available</h3>
            <p>DINCoordinator Address: {dincordinator_address}</p>
            <p>Genesis Model IPFS Hash: {genesis_model_ipfs_hash}</p>
          </div>
        ) : (
          <div>
            <h3>Genesis Model Not Available</h3>
            <button className="button button--primary" onClick={() => createGenesisModel()} style={{ marginTop: "1rem" }}>Create Genesis Model</button>
          </div>
        )}
        </>
      )}
      
    </div>
  );
}

/** ======================= Clients TAB ======================= */
function ClientsTab() {

  const [clientModelsCreatedF, setClientModelsCreatedF] = useState(false);
  const [client_model_ipfs_hashes, setClientModelIpfsHashes] = useState([]);
  const [clients_address, setClientsAddress] = useState([]);
  const { showTooltip } = useContext(TooltipContext);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchClientModelState = async () => {
      try {
        const response = await fetch("http://localhost:8000/clients/getClientModelsCreatedF", { method: "POST" });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(data);
        console.log("Initial clientModelsCreatedF state:", data.client_models_created_f);
        setClientModelsCreatedF(data.client_models_created_f);
        setClientModelIpfsHashes(data.client_model_ipfs_hashes);
        setClientsAddress(data.client_addresses);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching clientModelsCreatedF state:", err);
        showTooltip(err.message, true);
      }
    };

    fetchClientModelState();
  }, []);

  const createClientModels = async () => {
    try {
      const response = await fetch("http://localhost:8000/clients/createClientModels", { method: "POST" });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.message);
      
      // Show tooltip
      if (data.status === "success") {
        setClientModelsCreatedF(data.client_models_created_f);
        showTooltip(data.message, false);
      } else {
        showTooltip(data.message, true);
      }
    } catch (err) {
      console.error("Error creating client models:", err);
      // Show error tooltip
      showTooltip(err.message, true);
    }
  };

  return (
    <div className="tab-content">
      <h2>Clients</h2>
      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
        {clientModelsCreatedF ? (
        <div>
          <h3>Client Models Available</h3>
          {clients_address && clients_address.length > 0 ? (
            clients_address.map((address, index) => (
              <p key={index}>
                {address} : {client_model_ipfs_hashes[index]}
              </p>
            ))
          ) : (
            <p>No client models available.</p>
          )}
        </div>
      ) : (
        <div>
          <h3>Client Models Not Available</h3>
          <button className="button button--primary" onClick={() => createClientModels()} style={{ marginTop: "1rem" }}>Create Client Models</button>
        </div>
        )}
        </> 
      )}
      
    </div>
  );
}

/** ======================= Validator TAB ======================= */
function ValidatorsTab() {
  return (
    <div className="tab-content">
      <h2>Validators</h2>
    </div>
  );
}



function App() {
  const [activeTab, setActiveTab] = useState("ModelOwner");
  const { tooltipVisible, tooltipMsg, tooltipClass, hideTooltip, showTooltip } = useContext(TooltipContext);


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
      {/* Tooltip */}
      {tooltipVisible && (
        <div className={`tooltip ${tooltipClass}`} style={{ marginTop: "1rem", marginBottom: "1rem" }}>
          <span>{tooltipMsg}</span>
          <button onClick={hideTooltip} className="tooltip-close">
            &times;
          </button>
        </div>
      )}
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
          <TabBar activeTab={activeTab} setActiveTab={setActiveTab} />
          {activeTab === "ModelOwner" && <ModelOwnerTab />}
          {activeTab === "Clients" && <ClientsTab />}
          {activeTab === "Validators" && <ValidatorsTab />}
        </div>
      </main>

      <footer className="footer">
        <p>&copy; 2025 DIN MVP</p>
      </footer>
    </div>
  );
}

export default App;
