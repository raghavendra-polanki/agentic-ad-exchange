import ExchangeStats from '../components/ExchangeStats';
import DealFlow from '../components/DealFlow';
import AgentPanel from '../components/AgentPanel';

export default function Dashboard() {
  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Real-time exchange activity and agent status</p>
      </div>

      <ExchangeStats />

      <div className="dashboard-grid">
        <DealFlow />
        <AgentPanel />
      </div>
    </div>
  );
}
