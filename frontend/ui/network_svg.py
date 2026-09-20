"""Bounded, deterministic SVG layout for a small observed agent network.

No browser WASM/layout worker is needed on each live update. Every edge comes
from the normalized state; this diagram does not invent causal relationships.
"""
from collections import defaultdict
from html import escape
from .pets import LABELS

def network_svg(state):
    if not state.agents:
        return '<div class="network-wait" role="status">Waiting for the first agent update.</div>'
    rows=defaultdict(list)
    def depth(agent):
        seen={agent.id};parent=agent.parent_id;level=0
        while parent in state.agents and parent not in seen:
            seen.add(parent);level+=1;parent=state.agents[parent].parent_id
        if agent.role in {'critic','reviewer'} and level:level+=1
        return min(level,5)
    for agent in state.agents.values():rows[depth(agent)].append(agent)
    width=max(900,max(len(row) for row in rows.values())*205)
    height=max(280,(len(rows)-1)*155+150)
    positions={}
    for index,(_,agents) in enumerate(sorted(rows.items())):
        for column,agent in enumerate(agents):positions[agent.id]=((column+.5)*width/len(agents),65+index*155)
    edge_parts=[]
    for parent,child in sorted(state.edges):
        if parent not in positions or child not in positions:continue
        if state.agents[child].parent_id!=parent:continue
        x1,y1=positions[parent];x2,y2=positions[child]
        middle=(y1+y2)/2
        edge_parts.append(f'<path class="network-spawn" d="M{x1},{y1+29} C{x1},{middle} {x2},{middle} {x2},{y2-33}" marker-end="url(#pet-spawn-arrow)"/>')
    for (sender,recipient),count in sorted(state.talk.items()):
        if not count or sender not in positions or recipient not in positions:continue
        x1,y1=positions[sender];x2,y2=positions[recipient]
        if sender==recipient:continue
        bend=42 if x1<=x2 else -42
        middle=(y1+y2)/2
        alignment=state.agents[sender].alignment
        stance=alignment if alignment in {'supporting','challenging'} else 'neutral'
        edge_parts.append(f'<path class="network-message {stance}" d="M{x1+18},{y1} C{x1+bend+65},{middle} {x2+bend+65},{middle} {x2+18},{y2}" marker-end="url(#pet-talk-arrow)"><title>{escape(sender)} to {escape(recipient)}: {int(count)} message(s)</title></path>')
    node_parts=[]
    for agent in state.agents.values():
        x,y=positions[agent.id];label=LABELS.get(agent.role,agent.role.replace('_',' ').title())
        short=label if len(label)<=25 else label[:23]+'…'
        active=' network-active' if agent.id==state.active_id else ''
        status={'running':'Working','done':'Done','failed':'Failed','stopped':'Stopped'}.get(agent.status,agent.status)
        node_parts.append(f'<g class="network-node{active}" transform="translate({x-94},{y-29})"><title>{escape(label)} · {escape(agent.id)} · {escape(status)}</title><rect width="188" height="58" rx="12"/><text class="network-label" x="94" y="23">{escape(short)}</text><text class="network-status" x="94" y="43">{escape(status)} · {agent.activity} events</text></g>')
    description=f'{len(state.agents)} observed agents. Solid arrows show spawning and dashed arrows show recorded messages.'
    moving='' if state.complete else ' network-moving'
    return (f'<div class="network-canvas{moving}"><svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(description,quote=True)}" xmlns="http://www.w3.org/2000/svg">'
        '<defs><marker id="pet-spawn-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="var(--ui-muted)"/></marker>'
        '<marker id="pet-talk-arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="var(--ui-accent)"/></marker></defs>'
        +''.join(edge_parts)+''.join(node_parts)+'</svg></div>')
