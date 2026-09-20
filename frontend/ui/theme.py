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
from pathlib import Path
from .config import PROFILE

# -- agent groups ---------------------------------------------------------

PLANNER, SPECIALIST, CRITIC = "planner", "specialist", "critic"

ROLE_GROUP = PROFILE.role_groups

# (light hue, dark hue, opaque tint for Graphviz node fills)
GROUP_COLORS = {
    PLANNER: ("#2a78d6", "#3987e5", "#D6E6F8"),
    SPECIALIST: ("#1baf7a", "#199e70", "#D2F0E4"),
    CRITIC: ("#eb6834", "#d95926", "#FBDFD3"),
}

# Reserved. Never used for an agent.
STATUS = {
    "good": "var(--good)",
    "warning": "var(--warning)",
    "serious": "var(--serious)",
    "critical": "var(--critical)",
}

GRAPH_INK = "#111827"


def group_of(role: str) -> str:
    group = ROLE_GROUP.get(role, SPECIALIST)
    return group if group in GROUP_COLORS else SPECIALIST


def hue(role: str, dark: bool = False) -> str:
    light_hex, dark_hex, _tint = GROUP_COLORS[group_of(role)]
    return dark_hex if dark else light_hex


def tint(role: str) -> str:
    return GROUP_COLORS[group_of(role)][2]


# -- stylesheet -----------------------------------------------------------

CSS = """

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

"""

# The console uses a fixed dark surface so graph, native widgets and HTML agree.
CSS += """

.stApp {
 --ink:#f2f5ec; --ink-2:#b5bfb9; --ink-3:#8d9c94;
 --line:#2a3933; --raise:#14231d; --accent:#d6fb73;
 --planner:#6eacf4; --specialist:#60cba9; --critic:#fa9674;
 --good:#a7e77d; --warning:#f6c966; --serious:#ec835a; --critical:#ff8585;
 background:#0b1511; color:var(--ink); font-family:'Segoe UI',sans-serif;
}
[data-testid='stHeader'] {background:transparent;}
[data-testid='stMainBlockContainer'] {max-width:1500px;padding:2.4rem 3.2rem 4rem;}
[data-testid='stSidebar'] {background:#101c16;border-right:1px solid #2a3933;}
[data-testid='stSidebar'] * {color:#b5bfb9;}
[data-testid='stSidebar'] [data-testid='stSidebarContent'] {padding-top:1rem;}
.brand {font-weight:850;font-size:1.9rem;letter-spacing:-.07em;color:#d6fb73!important;margin-bottom:2.5rem;}
.brand span {display:block;font:10px ui-monospace,monospace;letter-spacing:.18em;margin-top:.45rem;color:#8d9c94;}
.sidebar-footer {margin-top:3rem;padding-top:1rem;border-top:1px solid #2a3933;font:10px/1.8 ui-monospace,monospace;letter-spacing:.1em;}
.hero {padding:.6rem 0 1.3rem;border-bottom:1px solid var(--line);margin-bottom:1.3rem;position:relative;}
.hero-top {display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:1.25rem;}
.eyebrow {font:600 10px ui-monospace,monospace;letter-spacing:.16em;color:var(--ink-3);}
.mode-badge {border:1px solid #53613d;border-radius:3px;padding:.35rem .55rem;color:#d6fb73;font:10px ui-monospace,monospace;letter-spacing:.1em;white-space:nowrap;}
.hd {font-size:clamp(2.8rem,4.6vw,5.2rem);font-weight:750;letter-spacing:-.065em;line-height:1.02;margin:0 0 1.2rem;max-width:1000px;}
.hd em {font-style:normal;color:#d6fb73;}
.sub {font-size:1rem;line-height:1.65;max-width:65ch;margin-bottom:0;}
.ask-label {font:600 10px ui-monospace,monospace;letter-spacing:.13em;margin-bottom:.5rem;}
.stTextArea textarea {background:#13241b!important;color:#edf5e7!important;border:1px solid #405541!important;border-radius:4px!important;font-size:1.15rem!important;line-height:1.4!important;}
.stTextArea textarea:disabled {-webkit-text-fill-color:#e4ecdd!important;opacity:1!important;}
.stButton button {border-radius:4px!important;background:#1b2c22;color:#e4ecdd;border:1px solid #405541;font-size:.75rem!important;letter-spacing:.025em;text-transform:none;min-height:3.2rem;transition:transform .18s,background .18s;}
.stButton button[kind='primary'] {background:#d6fb73!important;color:#14200b!important;border:1px solid #d6fb73!important;}
.stButton button:hover {transform:translateY(-2px);border-color:#d6fb73!important;}
.stButton button:focus-visible {outline:3px solid #f2f5ec!important;outline-offset:3px;}
[data-testid='stWidgetLabel'] p {color:#b5bfb9;}
[data-baseweb='select'] > div,[data-baseweb='input'],[data-baseweb='input'] input {background:#1a2a21;color:#f2f5ec;}
[data-baseweb='popover'] * {color:#142019;}
.run-heading {display:flex;justify-content:space-between;gap:1rem;font:10px ui-monospace,monospace;letter-spacing:.12em;color:var(--ink-3);margin:2.4rem 0 1rem;}
.run-heading span:last-child {color:#d6fb73;letter-spacing:0;}
.stages {display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-bottom:1.1rem;}
.stage {border-top:2px solid #293b30;padding:.6rem 0;font-size:.72rem;color:#819288;}
.stage b {font-family:ui-monospace,monospace;margin-right:.4rem;font-weight:400;}
.stage.reached {border-color:#d6fb73;color:#eff7e7;}
.run-question {font-size:1rem;margin-bottom:1rem;color:var(--ink-2);}
.stats {gap:0;border:1px solid var(--line);background:#101d16;border-radius:4px;}
.stat {border:0;border-right:1px solid var(--line);border-radius:0;background:none;padding:1rem 1.3rem;}
.stat:last-child {border-right:0;}
.stat .k {font:10px ui-monospace,monospace;letter-spacing:.12em;}
.stat .v {font-size:2.3rem;font-weight:500;letter-spacing:-.06em;margin:.2rem 0;}
.stat .n {font-size:.7rem;}
.rule {font:600 10px ui-monospace,monospace;letter-spacing:.13em;margin:1.7rem 0 1rem;}
.network-idle {height:285px;position:relative;overflow:hidden;background:radial-gradient(ellipse at center,#203624 0%,#101d16 68%);border:1px solid var(--line);border-radius:4px;}
.network-core {position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:.4rem;}
.network-core>span {font-size:3rem;color:#d6fb73;line-height:1.3;}
.network-core strong {font-size:.95rem;font-weight:550;}
.network-core small {font-size:.7rem;color:#98ac9e;}
.orbit {position:absolute;left:50%;top:50%;border:1px solid #415d36;border-radius:50%;transform:translate(-50%,-50%);}
.orbit-one {width:220px;height:220px;}
.orbit-two {width:340px;height:340px;border-style:dashed;opacity:.45;}
.satellite {position:absolute;font:9px ui-monospace,monospace;letter-spacing:.12em;color:#b6ceb9;background:#172b1e;border:1px solid #3b563f;padding:.45rem;}
.s-one {top:17%;left:10%;}.s-two {top:26%;right:6%;}.s-three {bottom:11%;left:20%;}
.conversation-empty {border:1px solid var(--line);border-radius:4px;min-height:285px;padding:1.4rem 1.6rem;box-sizing:border-box;background:#111f18;}
.conversation-empty h3 {font-size:1.65rem;font-weight:550;letter-spacing:-.04em;line-height:1.15;color:#e5eedf;padding:.65rem 0;}
.conversation-empty p {font-size:.82rem;color:var(--ink-2);line-height:1.6;}
.waiting-line {font:10px ui-monospace,monospace;color:#8d9c94;margin-top:1rem;}
.waiting-line span {display:inline-block;width:6px;height:6px;border-radius:50%;background:#8d9c94;margin-right:.6rem;}
.conversation-feed {max-height:390px;overflow:auto;padding:1rem 1.2rem;border:1px solid var(--line);background:#101d16;border-radius:4px;}
.msg {padding-bottom:.7rem;border-bottom:1px solid var(--line);}
.msg:last-child {border-bottom:0;margin-bottom:0;}
.msg .body {font-size:.8rem;line-height:1.6;}
.agent {border:1px solid var(--line);border-top:3px solid var(--g);border-radius:4px;padding:1rem;transition:background .2s;}
.agent:hover {background:#1b3024;}
.agent .role {font-weight:600;}
.agent .say {line-height:1.55;margin-top:.6rem;}
.find {border-radius:4px;padding:1.2rem;}.verdict {background:#18291d;border-radius:4px;padding:1.5rem;}
.verdict .body {font-size:1.1rem;line-height:1.65;}
[data-baseweb='tab-list'] {gap:1.4rem;border-bottom:1px solid var(--line);}
[data-baseweb='tab'] {color:#b5bfb9;background:transparent;font-size:.8rem;}
[data-baseweb='tab'][aria-selected='true'] {color:#d6fb73;}
[data-baseweb='tab-highlight'] {background:#d6fb73;}
[data-testid='stExpander'] {background:#14231d;color:#f2f5ec;border-color:#2a3933;}
[data-testid='stGraphVizChart'] {background:#101d16;border:1px solid #2a3933;padding:1rem;border-radius:4px;}
@media(max-width:900px) {[data-testid='stMainBlockContainer']{padding:2rem 1.2rem}.hero-top{align-items:flex-start;flex-direction:column}.hd{font-size:3.2rem}.stat{padding:.8rem}.stage{font-size:.65rem}}
@media(max-width:500px) {.hd{font-size:2.6rem}.stats{display:grid;grid-template-columns:1fr 1fr}.stat:nth-child(2){border-right:0}.run-heading{font-size:9px}.stage b{display:block;margin-bottom:.3rem}}
@media(prefers-reduced-motion:reduce) {*,*::before,*::after {animation:none!important;transition:none!important;scroll-behavior:auto!important;}}

"""
CSS += """
.file-chips {display:flex;gap:.5rem;flex-wrap:wrap;margin:.2rem 0 1.3rem;}
.file-chips span {font:11px ui-monospace,monospace;padding:.5rem .7rem;border:1px solid #38503d;background:#14291b;color:#c6ddc0;border-radius:3px;}
[data-testid='stFileUploaderDropzone'] {background:#14231d;border:1px dashed #536b46;color:#dcebd5;}
[data-testid='stFileUploaderDropzone'] * {color:#dcebd5;}
[data-testid='stCaptionContainer'] {color:#a7b7ab;opacity:1;}
"""
CSS += """
[data-testid='stRadio'] label,[data-testid='stRadio'] p {color:#dcebd5!important;}
[data-testid='stSelectbox'] input,[data-testid='stSelectbox'] button {background:#1a2a21!important;color:#edf5e7!important;}
[data-testid='stCaptionContainer'] p {color:#a7b7ab!important;}
[data-testid='stMultiSelect'] [data-tag],
[data-testid='stMultiSelect'] [data-tag] span,
[data-testid='stMultiSelect'] [data-tag] button {color:#14200b!important;}
h1.hd {overflow-wrap:anywhere;}
@media(max-width:600px) {h1.hd{font-size:clamp(2rem,8vw,2.6rem)!important}.hero-top{gap:.5rem}}
"""
CSS += """
.flow-brand {display:flex;justify-content:space-between;align-items:center;color:#d6fb73;font-weight:750;font-size:1.35rem;letter-spacing:-.03em;margin-bottom:1.6rem;}
.flow-brand span {font:10px ui-monospace,monospace;letter-spacing:.1em;color:#a7b7ab;}
.flow-stages {margin-bottom:1.8rem;}
[data-testid='stMarkdown']:has(.rule) {margin:1.7rem 0 1rem;}
[data-testid='stMarkdown']:has(.rule) > div {align-items:center;}
[data-testid='stMarkdown'] .rule {margin:0;}
[data-testid='stMarkdown']:has(.verdict) > div {position:relative;}
[data-testid='stMarkdown']:has(.verdict) [data-testid='stMarkdownContainer'] {width:100%;}
[data-testid='stMarkdown']:has(.verdict) > div > label {position:absolute;top:1.6rem;right:1.2rem;}
[data-testid='stMainBlockContainer'] {max-width:1180px;}
h1 {font-size:2rem!important;letter-spacing:-.035em!important;}
@media(max-width:600px) {.flow-brand span{display:none}.flow-stages .stage{font-size:.67rem}}
"""

CSS += """
.st-key-stage_navigation {margin-bottom:1.5rem;}
.st-key-stage_navigation button {min-height:3.5rem;white-space:normal;text-align:left;border-radius:4px!important;transition:background .15s,border-color .15s;}
.st-key-stage_navigation button[kind='primary'] {box-shadow:inset 0 -3px 0 #839f39;}
.st-key-stage_navigation button:disabled {background:#111c16!important;border-color:#26352c!important;color:#798b7f!important;opacity:.75;cursor:not-allowed;}
.st-key-stage_navigation button:focus-visible {outline:3px solid #f2f5ec!important;outline-offset:3px;}
@media(max-width:600px) {.st-key-stage_navigation [data-testid='stHorizontalBlock']{flex-wrap:nowrap!important;gap:.3rem}.st-key-stage_navigation [data-testid='stColumn']{min-width:0!important;flex:1!important}.st-key-stage_navigation button{padding:.4rem!important;font-size:.65rem!important;min-height:4.2rem}}
"""

CSS += """
.loading-status {display:flex;align-items:center;gap:.7rem;padding:.8rem 1rem;border:1px solid #435738;border-radius:4px;background:#18271a;color:#dcebd5;font-size:.9rem;}
.loading-status span {width:8px;height:8px;flex:none;border-radius:50%;background:#d6fb73;animation:beat 1.3s ease-in-out infinite;}
.loading-status {position:relative;overflow:hidden;}
.loading-status::after {content:'';position:absolute;bottom:0;left:0;width:34%;height:2px;background:linear-gradient(90deg,transparent,var(--accent),transparent);animation:loading-sweep 2s ease-in-out infinite;}
@keyframes loading-sweep {from{transform:translateX(-110%)}to{transform:translateX(400%)}}
@media(prefers-reduced-motion:reduce){.loading-status span{animation:none}}
"""

CSS += """
.skill-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.7rem;margin:.5rem 0 1rem;}
.skill-card {padding:1rem;border:1px solid #34493b;background:#142019;border-radius:5px;}
.skill-heading {display:flex;align-items:center;gap:.6rem;margin-bottom:.7rem;color:#eef4e8;}
.skill-icon {vertical-align:middle;flex-shrink:0;}
.perspective {display:inline-block;color:var(--perspective);border-left:3px solid var(--perspective);padding:0 .45rem;font-size:.72rem;font-weight:600;margin:.25rem 0;}
.skill-chips {display:flex;gap:.3rem;flex-wrap:wrap;margin-top:.5rem;}
.skill-chip {display:inline-flex;align-items:center;gap:.3rem;font-size:.68rem;color:#b9cbbd;border:1px solid #34493b;border-radius:3px;padding:.2rem .35rem;}
"""

CSS += """
/* Help sits outside the widget's layout. Hover never reflows its neighbours. */
[data-testid='stVerticalBlock']:has(> [data-testid='stElementContainer'] > [data-testid='stHtml'] > .trace-help-anchor) {position:relative;}
[data-testid='stElementContainer']:has(> [data-testid='stHtml'] > .trace-help-anchor) {
 position:absolute;top:.4rem;right:.25rem;width:1rem!important;height:1rem!important;margin:0!important;z-index:20;
}
.trace-help-anchor {display:block;width:1rem;height:1rem;line-height:1;}
.trace-help-trigger {display:block;box-sizing:border-box;width:1rem;height:1rem;padding:0;border:1.5px solid currentColor;border-radius:50%;background:transparent;color:var(--ink-3);cursor:help;font:700 11px/13px 'Segoe UI',sans-serif;}
.trace-help-trigger:focus-visible {outline:2px solid var(--accent);outline-offset:3px;border-radius:50%;}
.trace-help-text {
 visibility:hidden;opacity:0;pointer-events:auto;position:absolute;top:100%;right:0;
 width:min(340px,calc(100vw - 48px));padding:.65rem .85rem;border:1px solid var(--line);border-radius:5px;
 background:var(--raise);color:var(--ink);font:400 .85rem/1.5 'Segoe UI',sans-serif;
 text-transform:none;letter-spacing:normal;text-align:left;white-space:normal;
 box-shadow:0 4px 18px #0002;z-index:100000;transition:none;animation:none;
}
.trace-help-anchor:hover .trace-help-text,
.trace-help-trigger:focus-visible + .trace-help-text {visibility:visible;opacity:1;}
@media(hover:none) {.trace-help-trigger:focus + .trace-help-text {visibility:visible;opacity:1;}}
@supports(anchor-name:--trace-help) {
 .trace-help-text {position:fixed;top:anchor(bottom);right:anchor(right);margin-top:0;position-try-fallbacks:flip-block,flip-inline;}
}

.trace-help-anchor[data-help-dismissed="true"] .trace-help-text {visibility:hidden!important;opacity:0!important;}

/* Theme changes share geometry; only the paint below is theme-specific. */
.st-key-workspace_header {margin-bottom:1.4rem;border:1px solid transparent;border-radius:10px;padding:1.1rem 1.25rem;}
.st-key-workspace_header .flow-brand {margin:0;min-height:2rem;font-size:1.45rem;}
[data-testid='stTooltipContent'] {border:1px solid transparent;}
[data-testid='stGraphVizChart'] svg .edge text {fill:var(--ink-2);}
.st-key-workspace_header [data-testid='stToggle'] {padding-top:.2rem;}
.st-key-workspace_header [data-testid='stToggle'] p {font-size:.8rem;color:var(--ink-2);}
@media(max-width:700px) {
 .st-key-workspace_header [data-testid='stHorizontalBlock'] {flex-wrap:nowrap!important;align-items:center;}
 .st-key-workspace_header [data-testid='stColumn'] {min-width:0!important;}
 .st-key-workspace_header [data-testid='stColumn']:first-child {flex:1 1 0!important;}
 .st-key-workspace_header [data-testid='stColumn']:last-child {flex:0 0 145px!important;}
 .st-key-workspace_header [data-testid='stWidgetLabel'] {white-space:nowrap;}
 .st-key-workspace_header .flow-brand span {display:none;}
}
"""

CSS += """
/* Linked arguments remain a single reading column, with no hidden text clipping. */
.argument-trace {min-width:0;margin:.55rem 0 1rem;border:1px solid var(--line);border-radius:4px;background:var(--raise);color:var(--ink);}
.argument-trace > summary {box-sizing:border-box;min-height:44px;padding:.7rem .85rem;cursor:pointer;font-size:.85rem;line-height:1.5;overflow-wrap:anywhere;}
.argument-trace > summary:hover {background:var(--surface-hover,color-mix(in srgb,var(--ink) 6%,transparent));}
.argument-trace > summary:focus-visible {outline:2px solid var(--accent);outline-offset:3px;border-radius:4px;}
.argument-trace[open] > summary {border-bottom:1px solid var(--line);}
.argument-trace-path,.argument-trace-note {margin:.75rem .85rem;color:var(--ink-2);font-size:.8rem;line-height:1.6;overflow-wrap:anywhere;}
.argument-trace-turn {min-width:0;margin:.85rem;padding:.8rem;border:1px solid var(--line);border-radius:3px;}
.argument-trace-kicker {font-size:.8rem;font-weight:700;color:var(--ink);overflow-wrap:anywhere;}
.argument-trace-agent {margin:.35rem 0;color:var(--ink-2);font-size:.85rem;overflow-wrap:anywhere;}
.argument-trace-id {color:var(--ink-3);font-family:var(--mono,monospace);font-size:.75rem;line-height:1.5;overflow-wrap:anywhere;}
.argument-trace-text {margin-top:.75rem;font-size:.95rem;line-height:1.65;white-space:pre-wrap;overflow-wrap:anywhere;}
@media(max-width:600px) {.argument-trace-turn{margin:.6rem;padding:.65rem}.argument-trace-path,.argument-trace-note{margin:.65rem}}
"""

CSS += """
/* A completed run is available without taking focus from the current draft. */
.run-outcome-notice {min-width:0;padding:.85rem 1rem;border:1px solid var(--line);border-inline-start:3px solid var(--accent);border-radius:4px;background:var(--raise);color:var(--ink);}
.run-outcome-title {margin:0;font-size:.95rem;font-weight:650;line-height:1.5;overflow-wrap:anywhere;}
.run-outcome-detail {margin:.35rem 0 0;color:var(--ink-2);font-size:.85rem;line-height:1.6;overflow-wrap:anywhere;}
.run-outcome-notice,.run-outcome-notice * {animation:none;transition:none;}
@media(max-width:600px) {.run-outcome-notice{padding:.75rem}}
"""

# This palette is selected explicitly, independent of the OS colour preference.
# White reading surfaces remain quiet; the constellation belongs to the header.
ASTRAL_CSS = r"""
:root, .stApp {
 --ink:#162342; --ink-2:#425372; --ink-3:#586b89;
 --line:#cbd7ed; --raise:#ffffff; --accent:#3159cc;
 --planner:#2a65c5; --specialist:#13775e; --critic:#a44727;
 --good:#236337; --warning:#83500b; --serious:#a4441c; --critical:#b22d4a;
 --surface:#ffffff; --surface-soft:#f3f6fd; --surface-hover:#eaf0ff;
 --blue-violet:linear-gradient(120deg,#235dc9 0%,#4658ce 58%,#7951c3 100%);
 color-scheme:light;
}
.stApp {
 background:radial-gradient(ellipse at 96% 0%,#e3e4fc 0,transparent 35%),
            radial-gradient(ellipse at 0% 30%,#eaf2ff 0,transparent 40%),#f8faff;
 color:var(--ink);
}
[data-testid='stAppViewContainer'],[data-testid='stMain'] {background:transparent;}
[data-testid='stMainBlockContainer'] {color:var(--ink);}
[data-testid='stHeading'],[data-testid='stHeading'] h1,[data-testid='stHeading'] h2,
[data-testid='stHeading'] h3,[data-testid='stMarkdownContainer'],
[data-testid='stText'],[data-testid='stMetricLabel'],[data-testid='stMetricValue'] {color:var(--ink);}
[data-testid='stWidgetLabel'] p,[data-testid='stRadio'] label,[data-testid='stRadio'] p,
[data-testid='stCheckbox'] label,[data-testid='stCheckbox'] p,[data-testid='stToggle'] p,
[data-testid='stCaptionContainer'] p {color:var(--ink-2)!important;}
[data-testid='stCaptionContainer'] {color:var(--ink-2)!important;opacity:1!important;}
.stApp a {color:#2757c0;}
[data-testid='stSidebar'] {background:#edf2fd;border-color:var(--line);}
[data-testid='stSidebar'] * {color:var(--ink-2);}
.sidebar-footer {border-color:var(--line);}
.brand,.flow-brand,.hd em {color:#274ba9!important;}
.brand span,.flow-brand span {color:#43577f;}
.st-key-workspace_header {
 border-color:#c4d1ef;
 background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='620' height='112' viewBox='0 0 620 112'%3E%3Cg fill='%233d60b8' opacity='.32'%3E%3Ccircle cx='98' cy='21' r='1.1'/%3E%3Ccircle cx='145' cy='80' r='1.3'/%3E%3Ccircle cx='233' cy='25' r='.9'/%3E%3Ccircle cx='266' cy='76' r='1'/%3E%3Ccircle cx='342' cy='46' r='1.2'/%3E%3Ccircle cx='398' cy='90' r='1'/%3E%3Ccircle cx='473' cy='22' r='1.1'/%3E%3Ccircle cx='572' cy='81' r='1.4'/%3E%3C/g%3E%3Cg fill='%235552b0' opacity='.42'%3E%3Cpath d='m193 40 1.3 4.7 4.7 1.3-4.7 1.3-1.3 4.7-1.3-4.7-4.7-1.3 4.7-1.3z'/%3E%3Cpath d='m410 18 1 3.5 3.5 1-3.5 1-1 3.5-1-3.5-3.5-1 3.5-1z'/%3E%3Cpath d='m526 54 1.5 5.5 5.5 1.5-5.5 1.5-1.5 5.5-1.5-5.5-5.5-1.5 5.5-1.5z'/%3E%3C/g%3E%3Cpath d='m342 46 68-23 63-1 53 39 46 20' stroke='%236f7bbb' fill='none' opacity='.16'/%3E%3C/svg%3E"),
                  linear-gradient(115deg,#f4f8ff 0%,#e2edff 48%,#ebe4fb 100%);
 background-position:center right,center;background-repeat:no-repeat;
 box-shadow:0 6px 24px #3755a009;
}
.mode-badge {color:#3459a9;background:#edf2ff;border-color:#b7c7e9;}
.stTextArea textarea {
 background:#ffffff!important;color:var(--ink)!important;border-color:#9caed2!important;
 caret-color:#3159cc;
}
.stTextArea textarea:disabled {-webkit-text-fill-color:#52617d!important;background:#edf1f9!important;}
[data-baseweb='select'] > div,[data-baseweb='input'],[data-baseweb='input'] input,
[data-baseweb='base-input'],[data-baseweb='textarea'],
[data-testid='stSelectbox'] input,[data-testid='stSelectbox'] button,
[data-testid='stNumberInput'] input,[data-testid='stTextInput'] input {
 background:#ffffff!important;color:var(--ink)!important;border-color:#a7b7d7!important;
 caret-color:#3159cc;
}
[data-baseweb='select'] svg,[data-baseweb='input'] svg {fill:var(--ink-2);}
[data-testid='stSelectbox'] [role='group']:focus-within,
[data-testid='stMultiSelect'] [role='group']:focus-within,
.react-aria-ComboBox > [role='group']:focus-within {
 border-color:#3159cc!important;outline-color:#3159cc!important;
 box-shadow:0 0 0 2px #3159cc20!important;
}
[data-testid='stSelectbox'] input:focus,[data-testid='stMultiSelect'] input:focus {
 outline-color:#3159cc!important;
}
[data-baseweb='select'] [data-baseweb='tag'],[data-testid='stMultiSelect'] [data-tag] {
 background:#e3ebff!important;border-color:#b9cbed!important;
}
[data-testid='stMultiSelect'] [data-tag],[data-testid='stMultiSelect'] [data-tag] span,
[data-testid='stMultiSelect'] [data-tag] button {color:#254a98!important;}
[data-baseweb='popover'],[data-baseweb='popover'] > div,[data-baseweb='menu'],
[data-baseweb='popover'] ul,[role='listbox'],[role='option'] {
 background:#ffffff!important;color:#162342!important;border-color:#bdcbe7!important;
}
[data-baseweb='popover'] *,[data-baseweb='tooltip'] * {color:#162342!important;}
[data-baseweb='tooltip'] {background:#ffffff!important;box-shadow:0 4px 20px #20376322;}
[data-testid='stTooltipIcon'],[data-testid='stTooltipIcon'] button,
[data-testid='stTooltipIcon'] svg {color:#52688f!important;opacity:1!important;}
[data-testid='stTooltipIcon'] button:hover {color:#3159cc!important;}
[data-testid='stTooltipContent'] {background:#ffffff!important;color:#162342!important;border-color:#bdcbe7;box-shadow:0 4px 20px #20376322;}
[data-testid='stTooltipContent'] * {color:#162342!important;}
[data-testid='stTooltipIcon'] button[aria-label^='Help'] svg {stroke:#52688f!important;}
[role='option'][aria-selected='true'],[role='option']:hover {background:#e9efff!important;}
.stButton button,[data-testid='stDownloadButton'] button,
[data-testid='stFileUploaderDropzone'] button {
 background:#ffffff!important;color:#284572!important;border-color:#a6b8dc!important;
}
.stButton button[kind='primary'] {
 background:var(--blue-violet)!important;color:#ffffff!important;border-color:#3559c8!important;
 box-shadow:0 3px 10px #3555be17;
}
.stButton button[kind='primary'] p {color:#ffffff!important;}
.stButton button:hover,[data-testid='stDownloadButton'] button:hover {
 border-color:#3159cc!important;filter:none;background:#edf2ff!important;
}
.stButton button[kind='primary']:hover {background:linear-gradient(120deg,#194eaf,#6a41b7)!important;}
.stButton button:focus-visible,.st-key-stage_navigation button:focus-visible {
 outline:3px solid #486bd6!important;outline-offset:3px;
}
.stButton button:disabled,.st-key-stage_navigation button:disabled {
 background:#eaf0fa!important;border-color:#c1cde3!important;color:#60708b!important;opacity:.78;
}
.st-key-stage_navigation button[kind='primary'] {box-shadow:inset 0 -3px 0 #b6c6ff,0 3px 10px #3555be17;}
/* Streamlit 1.64 exposes React Aria selection state on the visible label. */
[data-testid='stCheckbox'] label:has(input[role='switch']) > div:first-of-type {
 background:#a8b9d5!important;
}
[data-testid='stCheckbox'] label[data-selected]:has(input[role='switch']) > div:first-of-type {
 background:var(--blue-violet)!important;
}
[data-testid='stCheckbox'] label:has(input[role='switch']) > div:first-of-type > div {
 background:#ffffff!important;box-shadow:0 1px 3px #20376330;
}
[data-testid='stCheckbox'] label:has(input[type='checkbox']:not([role='switch'])) > div:first-of-type {
 background:#ffffff!important;border-color:#91a7ca!important;
}
[data-testid='stCheckbox'] label[data-selected]:has(input[type='checkbox']:not([role='switch'])) > div:first-of-type {
 background:#3159cc!important;border-color:#3159cc!important;
}
[data-testid='stRadioOption'] > div > div:first-child {background:#91a7ca!important;}
[data-testid='stRadioOption'] > div > div:first-child > div {background:#ffffff!important;}
[data-testid='stRadioOption'][data-selected] > div > div:first-child {background:#3159cc!important;}
[data-testid='stCheckbox'] label[data-focus-visible],
[data-testid='stRadioOption'][data-focus-visible] {background:#e2ebff!important;outline:2px solid #486bd6;outline-offset:3px;}
[data-baseweb='slider'] [role='slider'] {background:#3159cc!important;}
[data-baseweb='slider'] [data-testid='stThumbValue'] {color:#3159cc!important;}
[data-testid='stFileUploaderDropzone'] {background:#f0f5ff;border-color:#8aabdf;color:var(--ink-2);}
[data-testid='stFileUploaderDropzone'] * {color:var(--ink-2);}
.file-chips span {background:#edf2ff;color:#315594;border-color:#bacced;}
[data-testid='stExpander'] {background:#ffffff;color:var(--ink);border-color:var(--line);}
[data-testid='stExpander'] details,[data-testid='stExpander'] summary {color:var(--ink);border-color:var(--line);}
[data-testid='stExpander'] details[open] > summary {background:#edf2ff!important;color:var(--ink)!important;}
[data-testid='stExpander'] summary:hover {color:#3159cc;}
[data-testid='stAlert'] {color:var(--ink);background:#eaf1ff;border-color:#bdcdef;}
[data-testid='stAlert'] p {color:var(--ink);}
[data-testid='stCode'],[data-testid='stCode'] pre {background:#eef3fc;color:#23375d;}
[data-baseweb='tab'] {color:var(--ink-2);}
[data-baseweb='tab'][aria-selected='true'] {color:#3159cc;}
[data-baseweb='tab-highlight'] {background:var(--blue-violet);}
[data-testid='stTab'][aria-selected='true'] p {color:#3159cc!important;}
[data-testid='stTab'] .react-aria-SelectionIndicator {background:var(--blue-violet)!important;}
.run-heading span:last-child {color:#3159cc;}
.stage {border-color:#c6d2e8;color:#52698e;}
.stage.reached {border-color:#4165d3;color:#244782;}
.stats,.conversation-feed,[data-testid='stGraphVizChart'] {background:#ffffff;border-color:var(--line);}
.network-idle {background:radial-gradient(ellipse at center,#e6e5fc 0%,#edf4ff 48%,#ffffff 80%);}
.network-core>span {color:#4165d3;}
.network-core small,.waiting-line {color:var(--ink-3);}
.waiting-line span {background:var(--ink-3);}
.orbit {border-color:#9cb4df;}
.satellite {color:#315594;background:#f6f8ff;border-color:#b9c9e5;}
.conversation-empty {background:#ffffff;}
.conversation-empty h3 {color:var(--ink);}
.agent,.find {background:#ffffff;}
.agent:hover {background:#f2f6ff;}
.verdict {background:linear-gradient(110deg,#ffffff,#f2f4ff);}
.skill-card {background:#ffffff;border-color:var(--line);}
.skill-heading {color:var(--ink);}
.skill-chip {color:#415777;border-color:#c5d2e8;background:#f7f9ff;}
.perspective {color:#415372;}
.loading-status {border-color:#aabfe7;background:#eef3ff;color:#284879;}
.loading-status span {background:#5364d5;}
"""


def stylesheet(theme: str = "client") -> str:
    """Ship both palettes once; a browser attribute selects colours without Python."""
    astral = ASTRAL_CSS if theme == "astral" else (
        '@scope (html[data-trace-theme="astral"]) {\n' + ASTRAL_CSS + '\n}' if theme == "client" else "")
    return "<style>\n" + _BASE_CSS + astral + "\n</style>"


def render_theme_control(default_theme: str = "dark") -> None:
    from streamlit.components.v2 import component
    assets = Path(__file__).resolve().parents[1] / "static"
    toggle = component("trace_theme_toggle",
        html=(assets / "theme.html").read_text(encoding="utf-8"),
        css=(assets / "theme.css").read_text(encoding="utf-8"),
        js=(assets / "theme.js").read_text(encoding="utf-8"))
    toggle(key="trace_theme", data={"defaultTheme": default_theme})


_BASE_CSS = CSS
# Kept for integrations importing the original default stylesheet constant.
CSS = stylesheet()
