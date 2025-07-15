import React, { useState, useEffect, useContext, useCallback } from "react";
import { TooltipContext } from "../context/TooltipContext";

export default function TetherFoundationTab() {

    const [loading, setLoading] = useState(true);
    const { showTooltip } = useContext(TooltipContext);
    const [tetherFoundationAddress, setTetherFoundationAddress] = useState(null);
    const [tetherFoundationEthBalance, setTetherFoundationEthBalance] = useState(null);
    const [tetherMockContractAddress, setTetherMockContractAddress] = useState(null);
    const [tetherMockContractSupply, setTetherMockContractSupply] = useState(null);
    const [tetherMockContractBalance, setTetherMockContractBalance] = useState(null);
    
    const fetchTetherFoundationState = async () => {
        try {
            setLoading(true);
            const response = await fetch("http://localhost:8000/tetherfoundation/getTetherFoundationState", { method: "GET" });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Initial Tether Foundation state:", data);
            setTetherFoundationAddress(data.tetherfoundation_address);
            setTetherFoundationEthBalance(data.tetherfoundation_eth_balance);
            setTetherMockContractAddress(data.tethermock_contract_address);
            setTetherMockContractSupply(data.tethermock_contract_supply);
            setTetherMockContractBalance(data.tethermock_contract_balance);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching Tether Foundation state:", err);
            // Optionally show an error tooltip
            showTooltip(err.message, true);
            setLoading(false);
        }
    };
    
    useEffect(() => {
        fetchTetherFoundationState();
    }, []);
    
    const deployTetherMockContract = async () => {
        try {
            const response = await fetch("http://localhost:8000/tetherfoundation/deployTetherMockContract", { method: "POST" });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log(data.message);
            
            // Show tooltip
            if (data.status === "success") {
                setTetherMockContractAddress(data.tethermock_contract_address);
                setTetherMockContractSupply(data.tethermock_contract_supply);
                setTetherMockContractBalance(data.tethermock_contract_balance);
                showTooltip(data.message, false);
            } else {
                showTooltip(data.message, true);
                setTetherMockContractAddress(null);
            }
        } catch (err) {
            console.error("Error creating Tether Mock Contract:", err);
            // Show error tooltip
            showTooltip(err.message, true);
        } finally {
            fetchTetherFoundationState();
            setLoading(false);
        }
    };
    
    return (
        <div className="tab-content">
            <h2>Tether Foundation</h2>
            {loading ? (
                <div>Loading...</div>
            ) : (
                <>
                <div>
                    <h3>Tether Foundation Representative Address: {tetherFoundationAddress}</h3>
                    <h3>Tether Foundation Representative ETH Balance: {tetherFoundationEthBalance}</h3>
                    {tetherMockContractAddress && <h3>Tether Foundation Representative USDT Balance: {tetherMockContractBalance}</h3>}
                    {tetherMockContractAddress && <h3>Tether Mock Contract Address: {tetherMockContractAddress}</h3>}
                    {tetherMockContractAddress && <h3>Tether Mock Contract Supply: {tetherMockContractSupply}</h3>}
                </div>

                {!tetherMockContractAddress && (
                    <button
                        className="button button--primary"
                        onClick={deployTetherMockContract}
                        style={{ marginTop: "1rem" }}
                    >
                        Deploy Tether Mock Contract
                    </button>
                )}
                </>
            )}
        </div>
    );
}
