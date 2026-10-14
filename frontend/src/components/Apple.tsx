import type { AgentSkin } from "../agents";

/** A 2D apple, drawn rather than rendered: flat vector shapes, one soft
 *  gradient for roundness, one specular highlight for the glass feel. */
export function Apple({ skin, id }: { skin: AgentSkin; id: string }) {
  const [light, dark] = skin.body;
  return (
    <svg className="apple" viewBox="0 0 100 108" aria-hidden>
      <defs>
        <radialGradient id={`body-${id}`} cx="36%" cy="28%" r="78%">
          <stop offset="0%" stopColor={light} />
          <stop offset="62%" stopColor={light} />
          <stop offset="100%" stopColor={dark} />
        </radialGradient>
        <linearGradient id={`gloss-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={skin.shine} stopOpacity="0.95" />
          <stop offset="100%" stopColor={skin.shine} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* stem + leaf */}
      <path d="M50 22 C50 14 48 9 44 5" stroke="#6b4a2f" strokeWidth="3.4"
        strokeLinecap="round" fill="none" />
      <path d="M51 17 C60 7 74 6 79 9 C76 19 64 24 51 17 Z" fill={skin.leaf} />
      <path d="M53 16 C61 12 70 10 76 10" stroke="rgba(255,255,255,.45)"
        strokeWidth="1.6" fill="none" strokeLinecap="round" />

      {/* the apple body: two lobes meeting at a dimple */}
      <path
        d="M50 24 C40 14 20 18 13 34 C5 52 14 82 30 95 C38 101 44 97 50 97
           C56 97 62 101 70 95 C86 82 95 52 87 34 C80 18 60 14 50 24 Z"
        fill={`url(#body-${id})`}
      />

      {/* specular pane — the liquid-glass catch of light */}
      <ellipse cx="33" cy="42" rx="14" ry="19" fill={`url(#gloss-${id})`}
        transform="rotate(-22 33 42)" />
      <ellipse cx="68" cy="76" rx="8" ry="11" fill="rgba(255,255,255,.18)"
        transform="rotate(-18 68 76)" />
    </svg>
  );
}
