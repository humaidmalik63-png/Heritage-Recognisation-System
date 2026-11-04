"""
Heritage & Monument Recognition System - Grounded Knowledge Engine Schemas
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)
Phase 6.3: Grounded Historical Knowledge Engine

Defines Pydantic schemas for:
  - Source citations (ASI, UNESCO, Ministry of Culture, Gazetteers)
  - Chronological timeline events
  - Architectural analyses and distinctive features
  - Cultural & religious significance
  - Preservation and statutory conservation records
  - Verified interesting facts
  - Complete Grounded Knowledge Records
  - Retrieval-First Q&A ("Ask the Archive") requests and grounded responses
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class CitationType(str, Enum):
    PRIMARY_SURVEY = "PRIMARY_SURVEY"
    UNESCO_DOSSIER = "UNESCO_DOSSIER"
    GAZETTEER_MEMOIR = "GAZETTEER_MEMOIR"
    EPIGRAPHICAL_RECORD = "EPIGRAPHICAL_RECORD"
    STATUTORY_LEGAL = "STATUTORY_LEGAL"
    ACADEMIC_MONOGRAPH = "ACADEMIC_MONOGRAPH"


class SourceCitation(BaseModel):
    citation_id: str = Field(..., description="Unique alphanumeric identifier e.g. CIT-TAJ-01")
    title: str = Field(..., description="Official title of the monograph, dossier, or survey")
    publisher: str = Field(..., description="Authoritative publisher e.g. Archaeological Survey of India (ASI)")
    author_or_editor: Optional[str] = Field(None, description="Author, surveyor, or editor")
    year_published: Optional[str] = Field(None, description="Publication year or era")
    url: Optional[str] = Field(None, description="Direct URL to official portal or catalog archive")
    citation_type: CitationType = Field(CitationType.PRIMARY_SURVEY, description="Category of citation")
    archive_ref: Optional[str] = Field(None, description="Official archive or registry identifier e.g. WHC #252")
    relevant_claim: Optional[str] = Field(None, description="Specific factual claim this source supports")


class HistoricalEvent(BaseModel):
    event_id: str = Field(..., description="Identifier e.g. EVT-TAJ-1631")
    year_or_era: str = Field(..., description="Historical year or era e.g. 1631 CE")
    title: str = Field(..., description="Title of the historical event")
    description: str = Field(..., description="Detailed description of the event")
    historical_actors: List[str] = Field(default_factory=list, description="Rulers, architects, or patrons involved")
    citation_id: str = Field(..., description="Source citation reference validating this event")


class ArchitecturalDetail(BaseModel):
    style_name: str = Field(..., description="Primary architectural style e.g. Mughal Architecture")
    school_or_period: Optional[str] = Field(None, description="Regional school or dynastic epoch")
    key_features: List[str] = Field(default_factory=list, description="Distinguishing structural signatures")
    construction_materials: List[str] = Field(default_factory=list, description="Stone, mortar, and pigments used")
    structural_significance: str = Field(..., description="Engineering or stylistic importance")
    citation_id: str = Field(..., description="Source citation validating the architectural analysis")


class CulturalSignificance(BaseModel):
    cultural_context: str = Field(..., description="Cultural role in Indian and global civilization")
    religious_or_symbolic_meaning: Optional[str] = Field(None, description="Religious or philosophical iconography")
    intangible_heritage: Optional[str] = Field(None, description="Associated festivals, rituals, or oral traditions")
    citation_id: str = Field(..., description="Source citation validating the cultural significance")


class PreservationRecord(BaseModel):
    unesco_status: Optional[str] = Field(None, description="UNESCO World Heritage designation & inscription year")
    national_protection: str = Field(..., description="Classification under AMASR Act 1958 or State Heritage Act")
    governing_body: str = Field(..., description="Managing circle e.g. ASI Northern Circle / State Directorate")
    current_condition: str = Field(..., description="Conservation status and condition assessment")
    key_conservation_initiatives: List[str] = Field(default_factory=list, description="Documented restoration efforts")
    citation_id: str = Field(..., description="Source citation validating preservation status")


class InterestingFact(BaseModel):
    fact_id: str = Field(..., description="Identifier e.g. FCT-TAJ-01")
    headline: str = Field(..., description="Catchy historical fact title")
    detail: str = Field(..., description="Verified historical fact text")
    citation_id: str = Field(..., description="Source citation validating this fact")


class GroundedKnowledgeRecord(BaseModel):
    monument_id: str = Field(..., description="Unique monument key matching catalog e.g. taj_mahal")
    monument_name: str = Field(..., description="Official monument title")
    alternate_names: List[str] = Field(default_factory=list, description="Vernacular or historic alternate names")
    location: str = Field(..., description="City and state")
    coordinates: Dict[str, float] = Field(..., description="Latitude and longitude coordinates")
    historical_overview: str = Field(..., description="Comprehensive source-backed historical overview")
    construction_period: str = Field(..., description="Dates of commissioning and completion")
    patron_or_dynasty: str = Field(..., description="Commissioning ruler, dynasty, or institution")
    principal_architect: Optional[str] = Field(None, description="Recorded architect or chief master builder")
    architectural_analysis: ArchitecturalDetail = Field(..., description="Detailed architectural breakdown")
    cultural_significance: CulturalSignificance = Field(..., description="Source-backed cultural importance")
    historical_timeline: List[HistoricalEvent] = Field(default_factory=list, description="Chronological event log")
    preservation_record: PreservationRecord = Field(..., description="Official conservation and legal framework")
    interesting_facts: List[InterestingFact] = Field(default_factory=list, description="Curated source-backed facts")
    citations: Dict[str, SourceCitation] = Field(..., description="Catalog of authoritative sources keyed by ID")
    last_verified: str = Field(..., description="ISO timestamp of curatorial verification")
    verification_status: str = Field("VERIFIED_BY_ASI_UNESCO", description="Curatorial audit status")


class AskKnowledgeRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Inquiry regarding the monument")
    context_filter: Optional[str] = Field(
        None,
        description="Optional filter: 'architecture', 'timeline', 'preservation', 'history'"
    )


class AskKnowledgeResponse(BaseModel):
    monument_id: str
    monument_name: str
    question: str
    answer: str
    citations: List[SourceCitation]
    grounded: bool = Field(True, description="True if answer is directly anchored in verified sources")
    evidence_sufficient: bool = Field(True, description="False if sources lack sufficient data to answer")
    answering_engine: str = Field(..., description="'GEMINI_2_5_FLASH_GROUNDED' or 'OFFLINE_CURATORIAL_RETRIEVAL'")
    confidence_assessment: str
    disclaimer: Optional[str] = None

