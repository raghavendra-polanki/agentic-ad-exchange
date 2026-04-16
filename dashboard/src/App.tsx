import { DealFlow } from "./components/DealFlow";
import { AgentPanel } from "./components/AgentPanel";
import { ExchangeStats } from "./components/ExchangeStats";
import "./App.css";

function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>AAX Exchange</h1>
        <span className="subtitle">Agentic Ad Exchange — Live Deal Flow</span>
      </header>
      <main className="main">
        <div className="deal-flow-section">
          <DealFlow />
        </div>
        <div className="sidebar">
          <ExchangeStats />
          <AgentPanel />
        </div>
      </main>
    </div>
  );
}

export default App;
