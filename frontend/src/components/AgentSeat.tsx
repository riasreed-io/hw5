import type { AgentSkin } from "../agents";
import { Apple } from "./Apple";

export type SeatState = "idle" | "working" | "done";

export interface SeatData {
  state: SeatState;
  saying: string;
  toolCount: number;
  tools: string[];
}

export function AgentSeat({ skin, data }: { skin: AgentSkin; data: SeatData }) {
  const { state, saying, toolCount } = data;
  return (
    <div className={`seat ${state} ${state !== "idle" ? "active" : ""}`}>
      <div className="apple-wrap">
        <div
          className="halo"
          style={{
            background: `radial-gradient(circle, ${skin.accent}55 0%, ${skin.accent}00 68%)`,
          }}
        />
        <Apple skin={skin} id={skin.key} />
      </div>

      <div className="nameplate">
        <div className="role">{skin.role}</div>
        <div className="variety">{skin.variety}</div>
      </div>

      <div className={`bubble ${state === "idle" ? "quiet" : ""}`}>
        {saying}
        {state === "working" && (
          <span className="typing">
            <i /><i /><i />
          </span>
        )}
      </div>

      <div className="counts">
        {toolCount > 0 ? `${toolCount} tool call${toolCount === 1 ? "" : "s"}` : "—"}
      </div>
    </div>
  );
}
