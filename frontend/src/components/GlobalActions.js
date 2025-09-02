import { TooltipContext } from "../context/TooltipContext";
import { useContext } from "react";

export default function GlobalActions({ onReset, onDistribute, isResetting, isDistributing }) {


    const { showTooltip } = useContext(TooltipContext);

    const oneClickSetup = async () => {
      try {

        const response = await fetch("http://localhost:8000/oneclicksetup", {
          method: "GET",
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        console.log(data);
        showTooltip(data.message, false);
        
      } catch (error) {
        showTooltip(error.message, true);
      }

  
  
    }


    return (
      <div className="margin-block">
        <button
          className="button button--danger margin-block-lr"
          onClick={onReset}
          disabled={isResetting}
        >
          {isResetting ? "Resetting..." : "Reset All"}
        </button>
        <button
          className="button button--primary margin-block-lr"
          onClick={onDistribute}
          disabled={isDistributing}
        >
          {isDistributing ? "Distributing..." : "Distribute Dataset"}
        </button>

        <button className="button button--primary margin-block-lr" onClick={() => oneClickSetup()}>One-Click Setup</button>
      </div>
    );
  }
  