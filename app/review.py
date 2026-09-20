"""Bounded proposal discussion, kept separate from scientific evidence findings."""
from app.agents.base import Agent
from app.models import Verdict
from app.skills import role_metadata


def supplied_inventory(bundle):
    """Bounded excerpts with original upload references, no relevance claims."""
    records = []
    known = {file.filename for file in bundle.files}
    for kind, rows in (("variant", bundle.variants), ("lab", bundle.labs), ("note", bundle.notes)):
        for row in rows[:3]:
            if row.source_file not in known:
                continue
            if kind == "variant":
                excerpt = f"{row.label}; chr{row.chrom}:{row.pos} {row.ref}>{row.alt}"
            elif kind == "lab":
                excerpt = f"{row.name}: {row.raw_value or row.value} {row.unit or ''}"
            else:
                excerpt = row.text[:350]
            source = {"kind": "file", "ref": row.source_file,
                      "locator": f"line {row.source_line}" if row.source_line else None,
                      "quote": excerpt if kind == "note" else None}
            records.append({"kind": kind, "excerpt": excerpt, "source": source})
    return records


class ReviewAgent(Agent):
    def __init__(self, role, ctx, discussion):
        super().__init__(f"{role}-1" if role != "critic" else "critic-0",
                         f"{role.title()} the proposed idea without claiming scientific validation.",
                         ctx, parent_id="orchestrator-0")
        self.role = role
        self.discussion = discussion
        self.phase = "opening"
        self.recipient = "orchestrator-0"

    async def investigate(self):
        prior = [dict(item) for item in self.discussion]
        inventory = supplied_inventory(self.ctx.bundle)
        if self.role == "research":
            text = (f"Supplied-input inventory for: {self.ctx.question}\n"
                    f"Available records: {self.ctx.bundle.summary()}. "
                    "This stage inventories inputs only; it performs no external research, source verification, or scientific validation.")
            if inventory:
                text += "\n" + "\n".join(f"{record['kind']}: {record['excerpt']} [{record['source']['ref']}, {record['source']['locator'] or 'record'}]" for record in inventory)
                text += "\nOnly up to three records per input type are shown; their relevance to the proposal remains unverified."
            else:
                text += "\nEvidence needed: a defined target, a baseline, independent evaluation data and a falsification criterion. Feasibility remains an assumption."
        else:
            task = (f"Idea review, {self.phase}: {self.ctx.question}. "
                    "Use the prior discussion. Supporter develops a testable proposal; challenger identifies assumptions "
                    "and counterexamples; revision must respond to the challenge; critic summarizes tradeoffs and next evidence. "
                    "All output is an unverified proposal, not scientific findings. Do not assert facts, invent citations, "
                    "claim validation or give diagnosis/treatment advice. Return a discussion message and no claims.")
            self.tool_call("reasoning.step", phase=self.phase, role=self.role)
            result = await self.ctx.providers.reasoning.step(self.role, task, {
                "task_mode": "idea_review", "phase": self.phase,
                "question": self.ctx.question, "discussion": prior,
                "input_inventory": inventory,
                "review_agent_statuses": self.ctx.extras.get("review_agent_statuses", {}),
            })
            text = result.message.strip()
            if not text:
                raise ValueError("Review provider returned an empty discussion message")
            self.tool_result("reasoning.step", {"phase": self.phase, "message": text})
        item = {
            "id": f"discussion-{len(self.discussion) + 1}", "agent_id": self.agent_id,
            "phase": self.phase, "alignment": role_metadata(self.role)["alignment"],
            "stance": role_metadata(self.role)["alignment"], "basis": "proposal",
            "text": text, "assumptions": ["Feasibility and scientific validity remain untested."],
            "evidence_refs": list(dict.fromkeys(record["source"]["ref"] for record in inventory)) if self.role == "research" else [],
            "provenance": [record["source"] for record in inventory] if self.role == "research" else [],
            "open_questions": ["What independent observation would falsify the proposal?"],
            "reply_to": prior[-1]["id"] if prior else None,
        }
        if self.role == "research" and inventory:
            item["basis"] = "source_grounded"
        self.discussion.append(item)
        self.ctx.bus.emit("agent_message", agent_id=self.agent_id, agent_role=self.role,
                          parent_id=self.recipient,
                          payload={"text": text, "discussion": item, "to": self.recipient})


async def run_discussion(agents):
    research, supporter, challenger = agents
    research.phase, research.recipient = "input_inventory", supporter.agent_id
    await research.run()
    supporter.phase, supporter.recipient = "opening", challenger.agent_id
    await supporter.run()
    challenger.phase, challenger.recipient = "challenge", supporter.agent_id
    await challenger.run()
    if supporter.status == "done" and challenger.status == "done":
        supporter.phase, supporter.recipient = "revision", "critic-0"
        await supporter.run()
    research.ctx.extras["review_agent_statuses"] = {agent.agent_id: agent.status for agent in agents}


class ReviewCritic(ReviewAgent):
    async def synthesize(self):
        self.phase = "summary"
        self.recipient = "orchestrator-0"
        await self.investigate()
        incomplete = any(status != "done" for status in self.ctx.extras.get("review_agent_statuses", {}).values())
        return Verdict(answer=("Idea review complete with missing contributions.\n\n" if incomplete else "Idea review complete.\n\n") + self.discussion[-1]["text"],
                       rationale="The critic reviewed the available recorded discussion. " + ("Agent failures left the exchange incomplete. " if incomplete else "") + "This is a proposal review, not scientific validation.",
                       confidence=0, abstained=True,
                       abstain_reason="Scientific validation is withheld: discussion is not independent evidence.",
                       caveats=["Arguments and suggestions are unverified proposals, not evidence or calibrated probabilities."])
