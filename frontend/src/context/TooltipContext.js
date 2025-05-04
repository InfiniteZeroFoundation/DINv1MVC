import React, { createContext, useState } from "react";

export const TooltipContext = createContext();

export const TooltipProvider = ({ children }) => {
  const [tooltipMsg, setTooltipMsg] = useState("");
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipClass, setTooltipClass] = useState("");
  const [tooltipTimeout, setTooltipTimeout] = useState(null);

  // Function to show tooltip with dynamic content and styling

  const showTooltip = (message, isError = false) => {
    setTooltipMsg(message); // Set the message content
    setTooltipClass(isError ? "message--error" : "message--success"); // Set the class (red/green)
    setTooltipVisible(true); // Show the tooltip

    // Clear any existing timeout to avoid conflicts
    if (tooltipTimeout) {
      clearTimeout(tooltipTimeout); // Cancel the previous timeout
    }

    // Set a new timeout to hide the tooltip after 3 seconds
    const timeout = setTimeout(() => {
      setTooltipVisible(false); // Hide the tooltip
      setTooltipTimeout(null); // Clear the reference to the timeout ID
    }, 3000);

    // Save the new timeout ID in the state
    setTooltipTimeout(timeout);
  };

  const hideTooltip = () => {
    setTooltipVisible(false);
    setTooltipMsg("");
  };

  return (
    <TooltipContext.Provider
      value={{ tooltipMsg, tooltipVisible, tooltipClass, showTooltip, hideTooltip }}
    >
      {children}
    </TooltipContext.Provider>
  );
};
