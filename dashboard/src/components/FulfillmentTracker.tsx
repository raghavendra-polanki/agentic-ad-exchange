interface FulfillmentStep {
  label: string;
  status: 'completed' | 'active' | 'pending';
}

interface FulfillmentTrackerProps {
  steps: FulfillmentStep[];
  dealId?: string;
}

export default function FulfillmentTracker({ steps, dealId }: FulfillmentTrackerProps) {
  return (
    <div className="fulfillment-tracker">
      <div className="card-header">
        <span className="card-title">Fulfillment Progress</span>
        {dealId && <code>{dealId.slice(0, 8)}</code>}
      </div>
      {steps.map((step, i) => (
        <div key={i} className="fulfillment-step">
          <div className={`fulfillment-step-dot ${step.status}`} />
          <span className={`fulfillment-step-label ${step.status}`}>
            {step.label}
          </span>
        </div>
      ))}
    </div>
  );
}
