import { useState } from "react";
import type { PaymentRequest } from "../types";

export function Approvals({
  requests,
  approver,
  onApprove,
}: {
  requests: PaymentRequest[];
  approver: string;
  onApprove: (id: number) => Promise<void>;
}) {
  const [busy, setBusy] = useState<number | null>(null);

  if (requests.length === 0) {
    return (
      <p className="empty">
        Nothing waiting. Agents can prepare a payment, but only you can release
        the money — requests land here when they do.
      </p>
    );
  }

  return (
    <>
      {requests.map((r) => (
        <div className="approval" key={r.id}>
          <div className="amt">${r.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="to">
            {r.kind === "rent" ? "Rent" : `Invoice ${r.ref_id}`} · {r.payee}
          </div>
          <div className="why">{r.reason}</div>
          <div className="acts">
            <button
              className="btn go"
              disabled={busy !== null}
              onClick={async () => {
                setBusy(r.id);
                try {
                  await onApprove(r.id);
                } finally {
                  setBusy(null);
                }
              }}
            >
              {busy === r.id ? "Releasing…" : "Approve & pay"}
            </button>
            <span className="counts">as {approver}</span>
          </div>
        </div>
      ))}
    </>
  );
}
