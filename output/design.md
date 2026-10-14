# Campus Customs Desk — design notes

The brief I set myself: this should feel like a desk someone would *want* to
sit at. Apple-inspired, minimal, slightly futuristic, liquid glass, and the
agents as apples — 2D and stylish rather than a cheesy 3D cartoon.

**Why that brief and not a dashboard of tables.** Five agents arguing about a
t-shirt is genuinely interesting to watch, and almost every agent UI throws
that away by rendering it as a log file. A desk you enjoy sitting at is one
where the state of the work is legible before you read a word — which apple is
awake, which is asleep, whether the balance just moved. The glass and the
animation are not decoration on top of that; they are how the state gets
communicated. Apple's design language is the reference because it does exactly
this: depth and motion carry meaning, and nothing is louder than the content.

---

## 1. The surface: liquid glass, not "frosted div"

Behind everything sits a slow-moving colour field — four blurred blobs in
blush, sky, apple-green and amber, drifting on 26–38 second loops. Nothing on
the page is a flat panel over a flat background; every surface is a pane with
that colour moving underneath it.

Each pane gets three things, which is what separates liquid glass from a grey
box with transparency:

- **Blur plus saturation.** `backdrop-filter: blur(28px) saturate(180%)` —
  the saturation boost is the important half. Blur alone turns colour to mud;
  pushing saturation keeps the field vivid through the glass, the way real
  frosted glass intensifies what is behind it.
- **A specular rim.** A one-pixel white inset highlight along the top edge and
  a fainter one along the bottom, so the pane has a lit edge where light
  catches it rather than a drawn border.
- **A sheen.** A diagonal white gradient over the top third of every pane,
  fading to nothing by 38%. This is what makes it read as a physical object
  tilted toward a light source.

Why: the shop's data is mostly small numbers and short sentences. A heavy UI
would bury it. Glass gives structure — you can see where one region ends and
another begins — without adding visual weight to compete with the content.

## 2. Layout: board, stage, rail

Three columns, left to right in the order you actually work:

- **The board (330px).** The three tickets, each a card you can press. Status
  chip top-right, requester, and the facts that matter (SKU · size × qty, or
  the rent amount and date). Selecting one lifts it and draws a blue inner
  ring rather than changing its colour — the card stays recognisable.
- **The stage (flexible).** Where the agents live and where the decision
  appears. This is the biggest region because watching the team work is the
  point of the product.
- **The rail (340px).** Money. Checking balance, then approvals, then the live
  trail. Everything financial is in one vertical strip so there is never a
  question of where to look when cash is involved.

The top bar carries only what must always be true: shop day, which model is
running, backend status, the balance, and reset.

## 3. The agents are apples

Five agents, five apple varieties, each a different hue so they are
distinguishable in peripheral vision while a run is moving:

| Agent | Variety | Why that colour |
|---|---|---|
| Boss | Red Delicious | Deepest, most saturated red — the one your eye lands on first |
| Inventory | Granny Smith | Green reads as "stock, shelves, physical goods" |
| Accounting | Golden Delicious | Gold for money, without resorting to a dollar sign |
| Facilities | Fuji | Blush-plum, the quietest of the five — it speaks least often |
| Customer Service | Honeycrisp | Warm pink, the friendliest, since it writes to people |

Each apple is hand-drawn SVG: one radial gradient for roundness, a tilted
white ellipse for the specular catch, a second smaller one low-right for
bounce light, a brown stem and a single leaf with a highlight stroke. Flat
vector, no 3D, no bevels — the same restraint as the rest of the page, and it
scales to any size without looking rendered.

**2D was a deliberate choice.** A 3D apple would be the loudest thing on
screen and would date immediately. A flat one with a single light source reads
as a designed mark, and it sits naturally next to glass, which is also a
light-and-transparency effect rather than a modelled one.

## 4. How the agents read differently

The whole point is seeing *who the Boss actually called*. So the three states
are deliberately unmistakable at a glance:

- **Idle** — 42% opacity, slightly desaturated, floating on a slow 5.5s bob.
  Present but asleep. An agent that was never needed stays visibly asleep for
  the whole run, which is exactly the thing worth noticing.
- **Working** — full colour, a 1.15s bob with a squash-and-stretch at the
  apex, and a coloured halo in that agent's own hue pulsing behind it. The
  speech bubble gains three animated typing dots.
- **Done** — a quick settle animation, then it holds still at full colour with
  its closing statement in the bubble.

The seat background lights up for any agent that is not idle, so the "who got
involved" answer is readable as a shape before you read a single word.

**Speech bubbles** are glass too, with a rotated square notch pointing at the
apple. They carry plain English, not JSON: tool names are translated through a
lookup, so `check_vendor_can_ship` shows as "checking the vendor" and
`save_draft_message` as "drafting to the customer". The agents narrate their
own work in words a shop owner would use.

## 5. Resolved tickets

Resolution shows up three ways, all quiet:

- The ticket's chip flips from amber **Open** to green **Resolved** with a
  leading check mark, and pops in on a springy curve the first time it changes
  — a single 0.6s animation, no confetti.
- The decision panel grows a matching Resolved chip next to its heading.
- The board's subtitle count updates ("2 open · 1 resolved").

Below the decision sits one line per agent — which tools it actually used on
this ticket — and the run's token cost. That summary survives a page reload,
because the board reconstructs it from the audit trail rather than from
whatever happened to be in memory.

## 6. How cash shows up

Money appears in two places at once, by design:

- **A pill in the top bar**, always visible, so the balance is never more than
  a glance away.
- **A large tabular figure in the rail**, with pending approvals underneath
  and "if you approve everything" below that — the number that actually tells
  you whether you can afford the next click.

When the balance drops after an approval, the pill flashes red and scales up
6% for 1.5 seconds, then settles. It is the only red in the interface and the
only thing that moves without being asked to. A balance that changes silently
is how a shop ends up overdrawn.

All figures use tabular numerals so digits do not jitter as they change.

**Approvals** are the one warm-tinted surface on the page: amber-edged glass
with the amount set large, who it goes to, why the agent asked, and a single
green "Approve & pay" button labelled with who is approving. The empty state
says the thing that matters — *agents can prepare a payment, but only you can
release the money*.

## 7. The live trail

Rather than hide the mechanics, the rail streams them: colour-coded tags for
tool calls (blue), delegations (purple), depth-limit refusals (red), and
payments (green). Watching `asks → tool → replies` scroll past while the
apples bob is what makes the system legible instead of magic.

## 8. Details that make it feel finished

- Buttons lift 1px on hover and compress on press, on Apple's standard
  `cubic-bezier(.2,.8,.2,1)` curve.
- The brand mark is the same apple silhouette as the agents, in near-black —
  the logo and the characters are one family.
- Section headings are small, uppercase, wide-tracked and grey; content is
  near-black. Hierarchy comes from weight and size, never from boxes.
- `prefers-reduced-motion` collapses every animation to 0.01ms. The drifting
  field and the bobbing apples are charming until they are not, and motion
  sensitivity is not an edge case.
- When the backend is unreachable the status dot turns red and the error names
  the exact command to start it, rather than saying "something went wrong".
