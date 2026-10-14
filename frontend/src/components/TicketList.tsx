import type { Ticket } from "../types";

const TYPE_LABEL: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Discount request",
};

export function TicketList({
  tickets,
  selected,
  runningId,
  justResolved,
  onSelect,
}: {
  tickets: Ticket[];
  selected: number | null;
  runningId: number | null;
  justResolved: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <>
      {tickets.map((t) => {
        const running = runningId === t.id;
        const resolved = t.status === "resolved";
        return (
          <button
            key={t.id}
            className={`ticket ${selected === t.id ? "sel" : ""}`}
            onClick={() => onSelect(t.id)}
          >
            <div className="row">
              <span className="id">#{t.id}</span>
              <span className="spacer" style={{ flex: 1 }} />
              <span
                className={`chip ${running ? "running" : resolved ? "resolved" : "open"} ${
                  justResolved === t.id ? "just" : ""
                }`}
              >
                {running ? "Running" : resolved ? "Resolved" : "Open"}
              </span>
            </div>
            <h3>{t.subject}</h3>
            <p>{t.requester}</p>
            <div className="meta">
              <span className="chip">{TYPE_LABEL[t.type] ?? t.type}</span>
              {t.sku && (
                <span className="chip">
                  {t.sku} · {t.size} × {t.qty}
                </span>
              )}
              {t.lease && <span className="chip">${t.lease.monthly_rent.toFixed(0)} due {t.lease.next_due}</span>}
            </div>
          </button>
        );
      })}
    </>
  );
}
