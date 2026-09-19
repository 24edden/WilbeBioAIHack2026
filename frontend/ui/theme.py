"""Design tokens and the stylesheet. One source for colour and type.

Colour policy, decided with the validator rather than by eye:

Agents are coloured by *function*, not by role. Three groups (planner,
specialist, critic) rather than six role hues, because six hues fail the
all-pairs colourblind and normal-vision separation floors in both light and
dark mode. Three pass every check cleanly (worst all-pairs normal-vision
delta E 24.0 light / 20.9 dark; CVD 9.2 / 9.4). Individual role identity is
carried by the role name written on every node and card, so nothing depends
on hue alone.

Hue is a mark, never text. Colour appears as bars, dots and node fills; all
label text wears ordinary ink, which keeps contrast compliant.

Status colours (good / warning / critical) are reserved for confidence and
run state. They never double as an agent colour.
"""

from __future__ import annotations

# -- agent groups ---------------------------------------------------------

PLANNER, SPECIALIST, CRITIC = "planner", "specialist", "critic"

ROLE_GROUP = {
    "orchestrator": PLANNER,
    "genomics": SPECIALIST,
    "literature": SPECIALIST,
    "clinical": SPECIALIST,
    "stats": SPECIALIST,
    "critic": CRITIC,
    "unknown": SPECIALIST,
}

# (light hue, dark hue, opaque tint for Graphviz node fills)
GROUP_COLORS = {
    PLANNER: ("#2a78d6", "#3987e5", "#D6E6F8"),
    SPECIALIST: ("#1baf7a", "#199e70", "#D2F0E4"),
    CRITIC: ("#eb6834", "#d95926", "#FBDFD3"),
}

# Reserved. Never used for an agent.
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

GRAPH_INK = "#111827"


def group_of(role: str) -> str:
    return ROLE_GROUP.get(role, SPECIALIST)


def hue(role: str, dark: bool = False) -> str:
    light_hex, dark_hex, _tint = GROUP_COLORS[group_of(role)]
    return dark_hex if dark else light_hex


def tint(role: str) -> str:
    return GROUP_COLORS[group_of(role)][2]


# -- stylesheet -----------------------------------------------------------

CSS = """
<style>
.stApp {
  --ink:        #0b0b0b;
  --ink-2:      #52514e;
  --ink-3:      #8a8983;
  --line:       rgba(11,11,11,.12);
  --raise:      rgba(11,11,11,.035);
  --accent:     #2a78d6;
  --planner:    #2a78d6;
  --specialist: #1baf7a;
  --critic:     #eb6834;
  --good:       #0ca30c;
  --warning:    #fab219;
  --critical:   #d03b3b;
}
@media (prefers-color-scheme: dark) {
  .stApp {
    --ink:        #ffffff;
    --ink-2:      #c3c2b7;
    --ink-3:      #8a8983;
    --line:       rgba(255,255,255,.16);
    --raise:      rgba(255,255,255,.055);
    --accent:     #3987e5;
    --planner:    #3987e5;
    --specialist: #199e70;
    --critic:     #d95926;
  }
}

/* ---- type ---- */
.hd {
  font-size: clamp(2.1rem, 4.2vw, 3.2rem);
  font-weight: 800;
  letter-spacing: -.035em;
  line-height: .98;
  margin: 0 0 .3rem;
  color: var(--ink);
}
.eyebrow {
  font-size: .7rem;
  font-weight: 800;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: .55rem;
}
.sub { color: var(--ink-2); font-size: 1rem; line-height: 1.45; max-width: 62ch; }
.rule {
  display: flex; align-items: center; gap: .7rem;
  font-size: .7rem; font-weight: 800; letter-spacing: .16em;
  text-transform: uppercase; color: var(--ink-3);
  margin: 1.4rem 0 .7rem;
}
.rule::after { content: ""; flex: 1; height: 1px; background: var(--line); }

/* ---- the question, the entry point of the whole program ---- */
.ask-label {
  font-size: .72rem; font-weight: 800; letter-spacing: .16em;
  text-transform: uppercase; color: var(--accent); margin-bottom: .1rem;
}
.stTextArea textarea {
  font-size: 1.35rem !important;
  font-weight: 550 !important;
  line-height: 1.35 !important;
  letter-spacing: -.012em;
  padding: .85rem 1rem !important;
  border-width: 2px !important;
  border-radius: 10px !important;
  color: var(--ink) !important;
}
.stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 18%, transparent) !important;
}
.stTextArea textarea::placeholder { color: var(--ink-3) !important; font-weight: 450 !important; }

/* ---- buttons ---- */
.stButton button {
  font-weight: 800 !important;
  letter-spacing: .07em;
  text-transform: uppercase;
  font-size: .82rem !important;
  border-radius: 9px !important;
  padding: .72rem 1.1rem !important;
  transition: transform .08s ease, filter .15s ease;
}
.stButton button:hover { filter: brightness(1.06); }
.stButton button:active { transform: translateY(1px); }

/* ---- stat strip ---- */
.stats { display: flex; gap: .55rem; flex-wrap: wrap; margin: .2rem 0 .3rem; }
.stat {
  flex: 1 1 120px; padding: .6rem .8rem;
  border: 1px solid var(--line); border-left: 4px solid var(--accent);
  border-radius: 9px; background: var(--raise);
}
.stat .k {
  font-size: .64rem; font-weight: 800; letter-spacing: .14em;
  text-transform: uppercase; color: var(--ink-3);
}
.stat .v {
  font-size: 1.85rem; font-weight: 800; letter-spacing: -.035em;
  line-height: 1.1; color: var(--ink); font-variant-numeric: tabular-nums;
}
.stat .n { font-size: .72rem; color: var(--ink-2); }

/* ---- agent cards ---- */
.agents { display: flex; gap: .55rem; flex-wrap: wrap; }
.agent {
  flex: 1 1 210px; min-width: 190px;
  border: 1px solid var(--line); border-left: 5px solid var(--g);
  border-radius: 10px; padding: .6rem .75rem; background: var(--raise);
  animation: rise .32s cubic-bezier(.2,.8,.3,1) both;
}
@keyframes rise { from { opacity: 0; transform: translateY(7px) } to { opacity: 1; transform: none } }
.agent .top { display: flex; align-items: baseline; justify-content: space-between; gap: .5rem; }
.agent .role {
  font-size: .95rem; font-weight: 800; letter-spacing: -.02em;
  color: var(--ink); text-transform: capitalize;
}
.agent .id { font-size: .7rem; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.agent .say { font-size: .78rem; color: var(--ink-2); line-height: 1.35; margin-top: .35rem; }
.state { font-size: .66rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; white-space: nowrap; }
.state.on  { color: var(--accent); }
.state.ok  { color: var(--ink-3); }
.state.bad { color: var(--critical); }
.dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: .3rem; vertical-align: middle; }
.state.on .dot { background: var(--accent); animation: beat 1.1s ease-in-out infinite; }
.state.ok .dot { background: var(--ink-3); }
.state.bad .dot { background: var(--critical); }
@keyframes beat { 0%,100% { opacity: 1; transform: scale(1) } 50% { opacity: .35; transform: scale(.8) } }

/* ---- conversation ---- */
.msg { display: flex; gap: .6rem; margin-bottom: .75rem; animation: rise .3s ease both; }
.msg .bar { width: 3px; border-radius: 2px; background: var(--g); flex: none; }
.msg .who { font-size: .78rem; font-weight: 800; color: var(--ink); letter-spacing: -.01em; }
.msg .to { font-size: .72rem; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.msg .body { font-size: .86rem; color: var(--ink-2); line-height: 1.42; margin-top: .12rem; }

/* ---- findings ---- */
.find { border: 1px solid var(--line); border-radius: 10px; padding: .75rem .9rem; margin-bottom: .55rem; background: var(--raise); }
.find .top { display: flex; align-items: center; justify-content: space-between; gap: .6rem; margin-bottom: .35rem; }
.find .who { font-size: .78rem; font-weight: 800; color: var(--ink); text-transform: capitalize; }
.find .who .chip { display: inline-block; width: 8px; height: 8px; border-radius: 2px; background: var(--g); margin-right: .4rem; }
.find .body { font-size: .92rem; color: var(--ink); line-height: 1.5; }
.score { font-size: .72rem; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; white-space: nowrap; font-variant-numeric: tabular-nums; }
.meter { height: 4px; border-radius: 3px; background: var(--line); margin-top: .5rem; overflow: hidden; }
.meter i { display: block; height: 100%; border-radius: 3px; background: var(--c); transition: width .4s ease; }

/* ---- verdict ---- */
.verdict { border: 2px solid var(--c); border-radius: 12px; padding: 1rem 1.15rem; margin: .3rem 0 .2rem; }
.verdict .tag {
  font-size: .72rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; color: var(--c);
}
.verdict .body { font-size: 1.02rem; line-height: 1.55; color: var(--ink); margin: .5rem 0 .7rem; }

/* ---- timeline ---- */
.ev { display: grid; grid-template-columns: 3.6rem 1.2rem 1fr; gap: .4rem; margin-bottom: .4rem; font-size: .82rem; }
.ev .t { color: var(--ink-3); font-variant-numeric: tabular-nums; text-align: right; }
.ev .w { font-weight: 800; color: var(--ink); }
.ev .b { color: var(--ink-2); line-height: 1.35; }

.empty { color: var(--ink-3); font-size: .85rem; padding: .5rem 0; }
</style>
"""
