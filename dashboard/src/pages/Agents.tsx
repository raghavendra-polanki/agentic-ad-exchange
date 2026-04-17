import AgentPanel from '../components/AgentPanel';

export default function Agents() {
  return (
    <div>
      <div className="page-header">
        <h1>Agent Directory</h1>
        <p>All registered supply and demand agents on the exchange</p>
      </div>

      <AgentPanel fullPage />
    </div>
  );
}
