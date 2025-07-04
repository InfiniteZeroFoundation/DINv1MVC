import React, { useState, useEffect, useContext } from "react";
import { TooltipContext } from "../context/TooltipContext";

/** ======================= DINDAO TAB ======================= */
export default function DINDAOTab() {

  const [loading, setLoading] = useState(true);
  const { showTooltip } = useContext(TooltipContext);
  const [dincordinator_address, setDincoordinatorAddress] = useState(null);
  const [dintoken_address, setDintokenAddress] = useState(null);
  const [DINDAORepresentative_address, setDINDAORepresentativeAddress] = useState(null);
  const [DINDAORepresentative_Eth_balance, setDINDAORepresentativeEthBalance] = useState(null);
  const [DINCoordinator_Eth_balance, setDINCoordinatorEthBalance] = useState(null);
  const [DinValidatorStake_address, setDinValidatorStakeAddress] = useState(null);

  const deployDinValidatorStake = async () => {
    try {
      const response = await fetch("http://localhost:8000/dindao/deployDinValidatorStake", { method: "POST" });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.message);
      
      // Show tooltip
      if (data.status === "success") {
        setDinValidatorStakeAddress(data.dinvalidatorstake_address);
        showTooltip(data.message, false);
      } else {
        showTooltip(data.message, true);
        setDinValidatorStakeAddress(null);
      }
    } catch (err) {
      console.error("Error creating DinValidatorStake:", err);
      // Show error tooltip
      showTooltip(err.message, true);
    }
  };

  const deployDINCoordinator = async () => {
    try {
      const response = await fetch("http://localhost:8000/dindao/deployDINCoordinator", { method: "POST" });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.message);
      
      // Show tooltip
      if (data.status === "success") {
        setDincoordinatorAddress(data.dincordinator_address);
        setDintokenAddress(data.dintoken_address);
        setDINDAORepresentativeAddress(data.DINDAORepresentative_address);
        setDINDAORepresentativeEthBalance(data.DINDAORepresentative_Eth_balance);
        setDINCoordinatorEthBalance(data.DINCoordinator_Eth_balance);
        
        showTooltip(data.message, false);
      } else {
        showTooltip(data.message, true);
        setDincoordinatorAddress(null);
        setDintokenAddress(null);
        setDINDAORepresentativeAddress(null);
        setDINDAORepresentativeEthBalance(null);
      }
    } catch (err) {
      console.error("Error creating DINDAO:", err);
      // Show error tooltip
      showTooltip(err.message, true);
    }
  };

  const fetchDINDAOState = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/dindao/getDINDAOState", { method: "POST" });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log("Initial DINDAO state:", data);
      setDincoordinatorAddress(data.dincordinator_address);
      setDintokenAddress(data.dintoken_address);
      setDINDAORepresentativeAddress(data.DINDAORepresentative_address);
      setDINDAORepresentativeEthBalance(data.DINDAORepresentative_Eth_balance);
      setDINCoordinatorEthBalance(data.DINCoordinator_Eth_balance);
      setDinValidatorStakeAddress(data.DINValidatorStake_address);
    
    } catch (err) {
      console.error("Error fetching DINDAO state:", err);
      // Optionally show an error tooltip
      showTooltip(err.message, true);
      setDincoordinatorAddress(null);
      setDintokenAddress(null);
      setDINDAORepresentativeAddress(null);
      setDINDAORepresentativeEthBalance(null);
      setDINCoordinatorEthBalance(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDINDAOState(); // Call the function when the component mounts
  },[]); // Add dependencies if necessary (e.g., showTooltip)

  return (
    <div className="tab-content">
      <h2>DINDAO</h2>
      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
        <div>
            <h3>DINDAO Representative Address: {DINDAORepresentative_address}</h3>
            <h3>DINDAO Representative ETH Balance: {DINDAORepresentative_Eth_balance}</h3>
            <h3>DINCoordinator Address: {dincordinator_address || "Not Available"}</h3>
            <h3>DINToken Address: {dintoken_address || "Not Available"}</h3>
            <h3>DINCoordinator ETH Balance: {DINCoordinator_Eth_balance ?? "Not Available"}</h3>
            <h3>DinValidatorStake Address: {DinValidatorStake_address || "Not Available"}</h3>
            {dintoken_address && !DinValidatorStake_address && (
              <button
                className="button button--primary"
                onClick={deployDinValidatorStake}
                style={{ marginTop: "1rem" }}
              >
                Deploy DinValidatorStake
              </button>
            )}
            {!dincordinator_address && (
              <button
                className="button button--primary"
                onClick={deployDINCoordinator}
                style={{ marginTop: "1rem" }}
              >
                Deploy DINCoordinator
              </button>
            )}
          </div>
        </> 
      )}
    </div>
  );
}

