"""Literature specialist — embedding search for supporting *and* contradicting
evidence.

This agent is the one that talks to another agent. It waits briefly on the
genomics specialist's first finding so that its query names the gene that was
actually found rather than whatever the user happened to type, then says so on
the bus — that message is the visible bit of inter-agent communication in the
demo, and it is real: remove the wait and the query changes.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import Agent
from app.corpus import cosine, document_text, documents
from app.hypothesis import mentioned_genes
from app.models import Provenance

PEER_WAIT_SECONDS = 12.0
RELEVANCE_FLOOR = 0.12
MAX_HITS = 5


class LiteratureAgent(Agent):
    role = "literature"

    async def investigate(self) -> None:
        query, peer_terms = await self._build_query()

        docs = documents()
        self.tool_call("bionemo.embed", n_documents=len(docs), query=query)
        vectors = await self.ctx.providers.bio.embed(
            [query] + [document_text(doc) for doc in docs]
        )
        query_vector, doc_vectors = vectors[0], vectors[1:]

        ranked: list[dict[str, Any]] = []
        for doc, vector in zip(docs, doc_vectors):
            score = cosine(query_vector, vector)
            if score < RELEVANCE_FLOOR:
                continue
            ranked.append({**doc, "score": round(score, 4)})
        ranked.sort(key=lambda hit: hit["score"], reverse=True)
        hits = ranked[:MAX_HITS]
        self.tool_result(
            "bionemo.embed",
            [{"pmid": h["pmid"], "score": h["score"]} for h in hits],
            n_above_floor=len(ranked),
        )

        step = await self.ctx.providers.reasoning.step(
            "literature",
            self.task,
            {
                "hits": hits,
                "query": query,
                "peer_terms": peer_terms,
                "hypothesis": self.ctx.hypothesis,
                "question": self.ctx.question,
            },
        )
        if step.message:
            self.say(step.message)

        by_pmid = {hit["pmid"]: hit for hit in hits}
        for claim in step.claims:
            hit = by_pmid.get(str((claim.detail or {}).get("pmid", "")), {})
            if not hit:
                self.say("Withheld a claim: its PMID was not present in the retrieved evidence.")
                continue
            provenance = [
                Provenance(
                    kind="pmid",
                    ref=str(hit.get("pmid", "unknown")),
                    locator=f"{hit.get('journal', '')} {hit.get('year', '')}".strip(),
                    quote=(hit.get("text", "")[:180] or None),
                )
            ]
            self.record(
                claim.claim,
                confidence=claim.confidence,
                provenance=provenance,
                stance=claim.stance,
                detail={"pmid": hit.get("pmid"), "score": hit.get("score"),
                        "tags": hit.get("tags", [])},
            )

    async def _build_query(self) -> tuple[str, list[str]]:
        """Question + hypothesis, widened by whatever genomics has found so far."""
        terms = [self.ctx.question]
        if self.ctx.hypothesis:
            terms.append(self.ctx.hypothesis)

        peers = await self.ctx.blackboard.wait_for("genomics", timeout=PEER_WAIT_SECONDS)
        peer_terms: list[str] = []
        if peers:
            for finding in peers:
                gene = (finding.detail or {}).get("gene")
                if gene and gene not in peer_terms:
                    peer_terms.append(gene)
                for extra in mentioned_genes(finding.claim):
                    if extra not in peer_terms:
                        peer_terms.append(extra)
            if peer_terms:
                self.say(
                    f"Picked up {', '.join(peer_terms)} from the genomics specialist; "
                    f"folding those into the search.",
                    to=peers[0].agent_id,
                )
                terms.extend(peer_terms)
        else:
            self.say(
                "No genomics findings within the wait window; searching on the question "
                "alone, which narrows what this search can rule out."
            )
        return " ".join(terms), peer_terms
