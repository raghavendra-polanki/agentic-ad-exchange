import { ExchangeStats } from "./components/ExchangeStats";
import { DealFlow } from "./components/DealFlow";
import { AgentPanel } from "./components/AgentPanel";
import "./App.css";

function App() {
  return (
    <div className="aax-dashboard">
      <header className="aax-header">
        <h1 className="aax-title">AAX</h1>
        <span className="aax-subtitle">Agentic Ad Exchange</span>
      </header>

      <ExchangeStats />

      <main className="aax-main">
        <div className="aax-left">
          <DealFlow />
        </div>
        <div className="aax-right">
          <AgentPanel />
        </div>
      </main>
    </div>
  );
}

export default App;
