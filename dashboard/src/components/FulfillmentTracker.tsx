import type { DealEvent } from "../types";

const FULFILLMENT_STEPS = [
  { key: "brief_generated", label: "Brief" },
  { key: "content_generating", label: "Content" },
  { key: "content_validating", label: "Validating" },
  { key: "content_approved", label: "Approved" },
  { key: "delivered", label: "Delivered" },
  { key: "completed", label: "Complete" },
];

export function FulfillmentTracker({ deal }: { deal: DealEvent }) {
  const fulfillmentStates = new Set(FULFILLMENT_STEPS.map((s) => s.key));
  const currentState = deal.fulfillment_state || deal.state;

  if (!fulfillmentStates.has(currentState) && currentState !== "deal_agreed") {
    return null; // Not in fulfillment
  }

  const currentIndex = FULFILLMENT_STEPS.findIndex(
    (s) => s.key === currentState,
  );

  return (
    <div className="fulfillment-tracker">
      <div className="fulfillment-label">Fulfillment</div>
      <div className="fulfillment-steps">
        {FULFILLMENT_STEPS.map((step, i) => (
          <div
            key={step.key}
            className={`fulfillment-step ${i <= currentIndex ? "done" : ""} ${i === currentIndex ? "current" : ""}`}
          >
            <div className="step-dot" />
            <span className="step-label">{step.label}</span>
          </div>
        ))}
      </div>
      {deal.validation && (
        <div className="validation-result">
          <span
            className={
              deal.validation.passed ? "validation-pass" : "validation-fail"
            }
          >
            Validation: {deal.validation.passed ? "Pass" : "Fail"} (
            {(deal.validation.score * 100).toFixed(0)}%)
          </span>
        </div>
      )}
      {deal.content_url && (
        <div className="content-link">Content: {deal.content_url}</div>
      )}
    </div>
  );
}
