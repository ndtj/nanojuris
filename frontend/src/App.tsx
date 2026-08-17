import React from "react";
import { createRoot } from "react-dom/client";
import Workbench from "./workbench/Workbench";
import "./styles.css";

function App() {
  React.useEffect(() => {
    document.title = "NanoJuris Studio";
  }, []);

  return <Workbench />;
}

createRoot(document.getElementById("root")!).render(<App />);
