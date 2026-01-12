from typing import List, Dict
from src.linking.embedder import EmbeddingEngine
from src.extraction.schema import ExtractedRule

class TraceabilityLinker:
    def __init__(self, similarity_threshold: float = 0.6):
        self.embedder = EmbeddingEngine()
        self.threshold = similarity_threshold

    def link(self, rules: List[ExtractedRule]) -> List[Dict]:
        """
        Build REGULATION → POLICY → SYSTEM traceability chains.
        """

        regs = [r for r in rules if r.doc_type == "REGULATION"]
        pols = [r for r in rules if r.doc_type == "POLICY"]
        syss = [r for r in rules if r.doc_type == "SYSTEM"]

        links = []

        for reg in regs:
            best_pol = self._best_match(reg, pols)
            best_sys = self._best_match(reg, syss)

            links.append({
                "regulation": reg,
                "policy": best_pol,
                "system": best_sys
            })

        return links

    def _best_match(self, source: ExtractedRule, candidates: List[ExtractedRule]):
        best = None
        best_score = 0.0

        for c in candidates:
            score = self.embedder.similarity(source.raw_text, c.raw_text)

            # Metric-based boost (important)
            if source.metric and source.metric == c.metric:
                score += 0.25  # strong signal

            # Dynamic thresholding
            threshold = self.threshold

            if source.doc_type == "REGULATION" and c.doc_type == "SYSTEM":
                threshold = 0.45  # system rules are terse / operational

            if score > best_score and score >= threshold:
                best_score = score
                best = { "rule": c, "score": round(min(score, 1.0), 3)}


        return best

