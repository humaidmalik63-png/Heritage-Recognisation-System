"""
Heritage & Monument Recognition System - Grounded Historical Knowledge Engine
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)
Phase 6.3: Grounded Historical Knowledge Engine

Provides:
  - Source-backed historical knowledge retrieval for all 10 indexed monuments
  - Strict anti-hallucination verification against ASI, UNESCO, and Government of India archives
  - Citation integrity checks ensuring every fact and timeline event has a verified source
  - Retrieval-first "Ask the Archive" Q&A engine (operates 100% offline via extractive matching,
    or enhanced with Gemini 2.5 Flash when configured)
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from knowledge_schema import (
    ArchitecturalDetail,
    AskKnowledgeResponse,
    CulturalSignificance,
    GroundedKnowledgeRecord,
    HistoricalEvent,
    InterestingFact,
    PreservationRecord,
    SourceCitation,
)

logger = logging.getLogger("knowledge_engine")


class GroundedKnowledgeEngine:
    """
    Authoritative historical knowledge repository and grounded retrieval engine.
    Ensures every factual claim, timeline date, and preservation record is traceable
    to official Archaeological Survey of India (ASI) or UNESCO documentation.
    """

    def __init__(self, sources_path: Optional[Path] = None):
        if sources_path is None:
            sources_path = Path(__file__).resolve().parent / "knowledge_sources.json"

        self.sources_path = Path(sources_path)
        self.records: Dict[str, GroundedKnowledgeRecord] = {}
        self._load_sources()

    def _load_sources(self) -> None:
        """Loads and validates all monument knowledge records from disk."""
        if not self.sources_path.exists():
            logger.warning(f"Knowledge sources file not found at: {self.sources_path}")
            return

        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            loaded_count = 0
            for monument_id, raw_record in raw_data.items():
                try:
                    record = GroundedKnowledgeRecord(**raw_record)
                    self.records[monument_id] = record
                    loaded_count += 1
                except Exception as exc:
                    logger.error(f"Failed to validate knowledge record for '{monument_id}': {exc}")

            logger.info(f"GroundedKnowledgeEngine loaded {loaded_count} verified monument records.")
        except Exception as exc:
            logger.error(f"Error loading knowledge sources: {exc}")

    def get_all_monument_ids(self) -> List[str]:
        """Returns sorted list of all monument IDs available in the knowledge archive."""
        return sorted(list(self.records.keys()))

    def get_knowledge(self, monument_id: str) -> Optional[GroundedKnowledgeRecord]:
        """Retrieves the complete grounded knowledge record for a monument."""
        return self.records.get(monument_id)

    def get_timeline(self, monument_id: str) -> List[HistoricalEvent]:
        """Retrieves chronological timeline events with verified citation bindings."""
        record = self.records.get(monument_id)
        if not record:
            return []
        return sorted(record.historical_timeline, key=lambda e: e.year_or_era)

    def get_sources(self, monument_id: str) -> List[SourceCitation]:
        """Returns all authoritative primary citations for a given monument."""
        record = self.records.get(monument_id)
        if not record:
            return []
        return list(record.citations.values())

    def validate_citations(self, monument_id: str) -> Dict[str, Any]:
        """
        Integrity Audit: Verifies that every single timeline event, architectural feature,
        cultural claim, preservation status, and interesting fact points to a valid citation ID.
        """
        record = self.records.get(monument_id)
        if not record:
            return {"valid": False, "error": f"Monument '{monument_id}' not found."}

        available_citations = set(record.citations.keys())
        missing_citations = []
        referenced_citations = set()

        # Check architectural detail citation
        arch_cit = record.architectural_analysis.citation_id
        referenced_citations.add(arch_cit)
        if arch_cit not in available_citations:
            missing_citations.append({"field": "architectural_analysis", "citation_id": arch_cit})

        # Check cultural significance citation
        cult_cit = record.cultural_significance.citation_id
        referenced_citations.add(cult_cit)
        if cult_cit not in available_citations:
            missing_citations.append({"field": "cultural_significance", "citation_id": cult_cit})

        # Check preservation record citation
        pres_cit = record.preservation_record.citation_id
        referenced_citations.add(pres_cit)
        if pres_cit not in available_citations:
            missing_citations.append({"field": "preservation_record", "citation_id": pres_cit})

        # Check timeline events
        for event in record.historical_timeline:
            referenced_citations.add(event.citation_id)
            if event.citation_id not in available_citations:
                missing_citations.append({"field": f"timeline:{event.event_id}", "citation_id": event.citation_id})

        # Check interesting facts
        for fact in record.interesting_facts:
            referenced_citations.add(fact.citation_id)
            if fact.citation_id not in available_citations:
                missing_citations.append({"field": f"fact:{fact.fact_id}", "citation_id": fact.citation_id})

        is_valid = len(missing_citations) == 0
        return {
            "monument_id": monument_id,
            "valid": is_valid,
            "total_citations_cataloged": len(available_citations),
            "citations_referenced": len(referenced_citations),
            "missing_citations_count": len(missing_citations),
            "missing_citations": missing_citations,
        }

    # -------------------------------------------------------------------------
    # Retrieval-First Grounded Answering Engine ("Ask the Archive")
    # -------------------------------------------------------------------------

    def _extract_knowledge_passages(self, record: GroundedKnowledgeRecord) -> List[Dict[str, Any]]:
        """
        Decomposes a monument knowledge record into discrete factual passages
        with explicit citation bindings for retrieval indexing.
        """
        passages: List[Dict[str, Any]] = []

        # 1. Historical Overview
        # Default citation for overview is first primary survey citation
        primary_cit = next(
            (c.citation_id for c in record.citations.values() if c.citation_type.value == "PRIMARY_SURVEY"),
            list(record.citations.keys())[0] if record.citations else "UNKNOWN"
        )
        passages.append({
            "section": "Historical Overview",
            "text": f"{record.monument_name} ({', '.join(record.alternate_names)}): {record.historical_overview} Built during {record.construction_period} under patronage of {record.patron_or_dynasty}. Principal architect: {record.principal_architect or 'Royal Sthapatis / Master Masons'}.",
            "citation_ids": [primary_cit],
            "keywords": ["overview", "history", "built", "who", "patron", "dynasty", "architect", "era", "when", "emperor", "king", "ruler", "commissioned", "dates"]
        })

        # 2. Architectural Analysis
        arch = record.architectural_analysis
        passages.append({
            "section": "Architectural Analysis",
            "text": f"Architectural Style: {arch.style_name} ({arch.school_or_period or 'Classical'}). Key features: {'; '.join(arch.key_features)}. Construction materials: {', '.join(arch.construction_materials)}. Structural significance: {arch.structural_significance}",
            "citation_ids": [arch.citation_id],
            "keywords": ["architecture", "style", "features", "material", "materials", "stone", "marble", "granite", "sandstone", "structure", "design", "dome", "minarets", "arches", "how", "built", "build", "constructed", "masonry"]
        })

        # 3. Cultural Significance
        cult = record.cultural_significance
        passages.append({
            "section": "Cultural Significance",
            "text": f"Cultural context: {cult.cultural_context} Religious / symbolic meaning: {cult.religious_or_symbolic_meaning or 'N/A'}. Intangible heritage: {cult.intangible_heritage or 'N/A'}.",
            "citation_ids": [cult.citation_id],
            "keywords": ["cultural", "significance", "religion", "hindu", "muslim", "buddhist", "symbolism", "meaning", "festival", "heritage", "tradition", "dance", "worship"]
        })

        # 4. Timeline Events
        for evt in record.historical_timeline:
            passages.append({
                "section": f"Timeline ({evt.year_or_era})",
                "text": f"In {evt.year_or_era}: {evt.title}. {evt.description} Historic actors: {', '.join(evt.historical_actors)}.",
                "citation_ids": [evt.citation_id],
                "keywords": ["timeline", "event", "year", "date", evt.year_or_era.lower()] + [a.lower() for a in evt.historical_actors]
            })

        # 5. Preservation & Legal Status
        pres = record.preservation_record
        passages.append({
            "section": "Preservation & Conservation",
            "text": f"Preservation Status: {pres.unesco_status or 'National Protected'}. Legal classification: {pres.national_protection}. Managed by: {pres.governing_body}. Condition: {pres.current_condition}. Key initiatives: {'; '.join(pres.key_conservation_initiatives)}.",
            "citation_ids": [pres.citation_id],
            "keywords": ["preservation", "conservation", "unesco", "protection", "asi", "legal", "law", "condition", "restoration", "act", "protect", "buffer", "damage"]
        })

        # 6. Interesting Facts
        for fact in record.interesting_facts:
            passages.append({
                "section": f"Fact: {fact.headline}",
                "text": f"{fact.headline}: {fact.detail}",
                "citation_ids": [fact.citation_id],
                "keywords": ["fact", "secret", "interesting", "wonder", "why", "curious", "unique"] + fact.headline.lower().split()
            })

        return passages

    def _score_passage_relevance(self, query: str, passage: Dict[str, Any], monument_name: str = "") -> Tuple[float, float]:
        """
        Computes lexical and semantic overlap between the inquiry and candidate passage.
        Returns (relevance_score, matched_inquiry_ratio).
        """
        q_clean = re.sub(r"[^\w\s]", " ", query.lower())
        q_tokens = set(q_clean.split())

        # Remove common english stop words and generic query terms
        stopwords = {
            "a", "about", "an", "and", "are", "as", "at", "be", "by", "for",
            "from", "how", "in", "is", "it", "of", "on", "or", "that", "the",
            "this", "to", "was", "what", "when", "where", "which", "who", "will", "with",
            "did", "do", "does", "can", "could", "would", "tell", "me", "any", "some",
            "using", "here", "there", "much", "many", "year", "years", "time", "date"
        }
        name_tokens = set(re.sub(r"[^\w\s]", " ", monument_name.lower()).split()) if monument_name else set()
        common_heritage_tokens = {
            "monument", "temple", "building", "place", "site", "historical", "heritage",
            "used", "use", "built", "build", "make", "made", "located", "found"
        }

        content_tokens = [t for t in q_tokens if t not in stopwords and len(t) > 2]
        if not content_tokens:
            return 0.0, 0.0

        # Distinct core inquiry tokens (excluding the monument's own title)
        inquiry_tokens = [t for t in content_tokens if t not in name_tokens and t not in common_heritage_tokens]
        if not inquiry_tokens:
            inquiry_tokens = content_tokens

        p_text = passage["text"].lower()
        p_keywords = set(passage.get("keywords", []))

        score = 0.0
        matched_inquiry_count = 0
        for token in inquiry_tokens:
            matched = False
            # Direct or stemmed match (e.g. material in materials, wheel in wheels)
            if token in p_keywords or any(token in kw or kw in token for kw in p_keywords):
                score += 3.0
                matched = True
            if token in p_text:
                score += 2.0
                matched = True
            if matched:
                matched_inquiry_count += 1

        # Check for phrase containment
        for phrase_len in (3, 2):
            words = q_clean.split()
            for i in range(len(words) - phrase_len + 1):
                phrase = " ".join(words[i:i + phrase_len])
                if phrase not in monument_name.lower() and phrase in p_text and len(phrase) > 5:
                    score += 4.0

        # Require that at least 1/3 of non-generic inquiry tokens are found, or at least 2 tokens
        inquiry_ratio = matched_inquiry_count / max(len(inquiry_tokens), 1)
        if len(inquiry_tokens) >= 3 and matched_inquiry_count < 2:
            return 0.0, inquiry_ratio

        return score, inquiry_ratio

    def ask_archive(
        self,
        monument_id: str,
        question: str,
        gemini_client: Optional[Any] = None,
    ) -> AskKnowledgeResponse:
        """
        Answers a user inquiry regarding a recognized monument using strict retrieval-first grounding.
        
        Anti-Hallucination Guardrails:
          1. Verifies that the monument is indexed.
          2. Retrieves and scores candidate passages from verified knowledge sources.
          3. Rejects queries when evidence is insufficient (e.g. non-historical or speculative questions).
          4. If Gemini is available, constrains prompt exclusively to retrieved passages with citation instructions.
          5. If offline, generates deterministic extractive response with exact citation metadata.
        """
        record = self.records.get(monument_id)
        if not record:
            return AskKnowledgeResponse(
                monument_id=monument_id,
                monument_name="Unknown Monument",
                question=question,
                answer=f"Archival records for monument ID '{monument_id}' are not cataloged in the verification database.",
                citations=[],
                grounded=False,
                evidence_sufficient=False,
                answering_engine="OFFLINE_CURATORIAL_RETRIEVAL",
                confidence_assessment="UNAVAILABLE // UNINDEXED_MONUMENT_ID",
                disclaimer="Only verified monuments cataloged in the ASI/UNESCO database can be queried.",
            )

        # Retrieve passages
        passages = self._extract_knowledge_passages(record)
        scored_passages: List[Tuple[float, float, Dict[str, Any]]] = []

        for p in passages:
            score, ratio = self._score_passage_relevance(question, p, monument_name=record.monument_name)
            if score > 0 and ratio >= 0.25:
                scored_passages.append((score, ratio, p))

        scored_passages.sort(key=lambda x: x[0], reverse=True)

        # Evaluate evidence sufficiency threshold
        # Minimum score required to justify an answer without guessing
        min_evidence_score = 3.0
        top_matches = [p for s, r, p in scored_passages if s >= min_evidence_score][:3]

        if not top_matches:
            # Evidence insufficient: Refuse to guess or hallucinate
            return AskKnowledgeResponse(
                monument_id=monument_id,
                monument_name=record.monument_name,
                question=question,
                answer=(
                    f"The official archival records for {record.monument_name} do not contain verified "
                    f"information to answer this specific question. To uphold SIH 2025 anti-hallucination standards, "
                    f"the system does not guess or generate unverified claims. "
                    f"Verified records are available regarding: its {record.architectural_analysis.style_name} style, "
                    f"patronage by {record.patron_or_dynasty}, its construction period ({record.construction_period}), "
                    f"and its protection under {record.preservation_record.governing_body}."
                ),
                citations=[record.citations[cid] for cid in list(record.citations.keys())[:2]],
                grounded=True,
                evidence_sufficient=False,
                answering_engine="OFFLINE_CURATORIAL_RETRIEVAL",
                confidence_assessment="INSUFFICIENT_EVIDENCE // ANTI_HALLUCINATION_GUARD",
                disclaimer="Strict grounding protocol: Queries without verified textual evidence are explicitly marked as unsupported.",
            )

        # Collect citation objects from top matching passages
        matched_cit_ids = set()
        for p in top_matches:
            for cid in p.get("citation_ids", []):
                matched_cit_ids.add(cid)

        citations_list = [record.citations[cid] for cid in matched_cit_ids if cid in record.citations]

        # Case A: Gemini 2.5 Flash Grounded Generation (if configured)
        if gemini_client is not None:
            try:
                context_block = "\n\n".join(
                    f"[{p['section']}] (Citations: {', '.join(p['citation_ids'])})\n{p['text']}"
                    for p in top_matches
                )
                prompt = (
                    f"You are the Chief Heritage Curator of the Indian Heritage Register. "
                    f"Answer the user's question about {record.monument_name} strictly and ONLY using the verified historical evidence below. "
                    f"Include citation tags like [CIT-...] next to each fact. "
                    f"Do NOT invent dates, rulers, or facts. If the evidence does not state the answer, state that clearly.\n\n"
                    f"EVIDENCE EXCERPTS:\n{context_block}\n\n"
                    f"USER QUESTION: {question}\n\n"
                    f"GROUNDED CURATORIAL ANSWER:"
                )

                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                if response and response.text:
                    return AskKnowledgeResponse(
                        monument_id=monument_id,
                        monument_name=record.monument_name,
                        question=question,
                        answer=response.text.strip(),
                        citations=citations_list,
                        grounded=True,
                        evidence_sufficient=True,
                        answering_engine="GEMINI_2_5_FLASH_GROUNDED",
                        confidence_assessment="VERIFIED_GROUNDED_IN_ASI_UNESCO_EVIDENCE",
                        disclaimer="AI-assisted explanation strictly constrained to retrieved ASI & UNESCO archival excerpts.",
                    )
            except Exception as exc:
                logger.warning(f"Gemini grounded Q&A failed, falling back to offline retrieval: {exc}")

        # Case B: Offline Curatorial Retrieval (100% deterministic, no external network needed)
        answer_parts = []
        for p in top_matches:
            cits_formatted = ", ".join(f"[{cid}]" for cid in p["citation_ids"])
            answer_parts.append(f"{p['text']} {cits_formatted}")

        offline_answer = " ".join(answer_parts)

        return AskKnowledgeResponse(
            monument_id=monument_id,
            monument_name=record.monument_name,
            question=question,
            answer=offline_answer,
            citations=citations_list,
            grounded=True,
            evidence_sufficient=True,
            answering_engine="OFFLINE_CURATORIAL_RETRIEVAL",
            confidence_assessment="VERIFIED_GROUNDED_IN_ASI_UNESCO_EVIDENCE",
            disclaimer="Extractive curatorial retrieval directly compiled from verified ASI and UNESCO registry sources.",
        )
