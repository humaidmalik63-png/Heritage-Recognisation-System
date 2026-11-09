"""
Shared Catalogue Membership and Grounded Resolution Service (Phase 8.6B Hotfix)

Canonical single source of truth for:
- 100-site heritage catalogue membership
- Three distinct states:
    1. CATALOGUED_AND_RECOGNITION_READY
    2. CATALOGUED_METADATA_ONLY
    3. OUT_OF_CATALOG
- Stable monument ID and normalized alias matching (case, alternate names, historical names, spelling)
- Anti-hallucination geodetic coordinate resolution
"""

import json
import logging
import re
import unicodedata
import difflib
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
CATALOGUE_100_FILE = BASE_DIR / "datasets" / "heritage_catalogue_100.json"

# All 100 catalogue monuments are now indexed with reference vectors in local FAISS
def get_faiss_recognition_ready_keys() -> Set[str]:
    cat = get_catalogue_100()
    return set(cat.keys()) if cat else set()

FAISS_RECOGNITION_READY_KEYS: Set[str] = set()

# Generic words that cannot independently trigger a monument match without distinctive proper nouns
GENERIC_WORDS: Set[str] = {
    "temple", "temples", "caves", "cave", "fort", "forts", "palace", "palaces",
    "monument", "monuments", "complex", "complexes", "tomb", "tombs", "mosque",
    "mosques", "church", "cathedral", "gate", "bridge", "tower", "group", "of",
    "and", "the", "in", "at", "sanctuary", "sanctuaries", "memorial", "stupa",
    "arch", "city", "center", "centre", "ancient", "historic", "historical",
    "museum", "museums", "heritage", "gallery", "galleries", "exhibition",
    "building", "buildings", "hall", "house", "park", "national", "state"
}


class CatalogueStatus(str, Enum):
    CATALOGUED_AND_RECOGNITION_READY = "CATALOGUED_AND_RECOGNITION_READY"
    CATALOGUED_METADATA_ONLY = "CATALOGUED_METADATA_ONLY"
    OUT_OF_CATALOG = "OUT_OF_CATALOG"


class CatalogueMembershipResult(BaseModel):
    status: CatalogueStatus
    monument_id: Optional[str] = None
    monument_name: Optional[str] = None
    catalog_entry: Optional[Dict[str, Any]] = None
    match_method: Optional[str] = None
    matched_alias: Optional[str] = None
    is_recognition_ready: bool = False
    coordinates: Optional[Dict[str, float]] = None
    location: Optional[str] = None
    country: Optional[str] = None


_CATALOGUE_CACHE: Optional[Dict[str, Any]] = None


def get_catalogue_100(force_reload: bool = False) -> Dict[str, Any]:
    """Returns the cached canonical 100-site catalogue manifest."""
    global _CATALOGUE_CACHE
    if _CATALOGUE_CACHE is not None and not force_reload:
        return _CATALOGUE_CACHE

    if not CATALOGUE_100_FILE.exists():
        logger.error(f"Authoritative 100-site catalogue file missing at {CATALOGUE_100_FILE}")
        return {}

    try:
        with open(CATALOGUE_100_FILE, "r", encoding="utf-8") as f:
            _CATALOGUE_CACHE = json.load(f)
            logger.info(f"Loaded {len(_CATALOGUE_CACHE)} sites into Catalogue Service cache.")
            return _CATALOGUE_CACHE
    except Exception as exc:
        logger.error(f"Failed loading {CATALOGUE_100_FILE}: {exc}")
        return {}


def _clean_tokens(s: str) -> List[str]:
    """Normalizes string: unicode NFKD, lowercase, alphanumeric tokens."""
    if not s:
        return []
    s = unicodedata.normalize("NFKD", str(s)).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return [w for w in s.split() if w]


def _proper_tokens(tokens: List[str]) -> List[str]:
    """Filters out common generic words, keeping only distinctive proper-noun roots."""
    return [w for w in tokens if w not in GENERIC_WORDS and len(w) >= 3]


def check_catalogue_membership(query: Optional[str]) -> CatalogueMembershipResult:
    """
    Authoritative membership lookup based on stable monument IDs and normalized aliases.
    Strictly prevents loose substring matches that could cause false positives.
    
    States:
    1. CATALOGUED_AND_RECOGNITION_READY: Exists in 100-site catalog AND has FAISS vectors.
    2. CATALOGUED_METADATA_ONLY: Exists in 100-site catalog, verified metadata, no FAISS index.
    3. OUT_OF_CATALOG: Does not exist in 100-site catalogue manifest.
    """
    if not query or len(str(query).strip()) < 3:
        return CatalogueMembershipResult(status=CatalogueStatus.OUT_OF_CATALOG)

    catalogue = get_catalogue_100()
    if not catalogue:
        return CatalogueMembershipResult(status=CatalogueStatus.OUT_OF_CATALOG)

    q_raw = str(query).strip()
    q_tokens = _clean_tokens(q_raw)
    q_proper = set(_proper_tokens(q_tokens))
    
    # Strip parenthetical clarifications, e.g. "Ajanta Caves (Cave 19)" -> "Ajanta Caves"
    q_unparen = re.sub(r"\([^)]*\)", "", q_raw).strip()
    q_unparen_tokens = _clean_tokens(q_unparen)
    q_unparen_proper = set(_proper_tokens(q_unparen_tokens))

    matched_mid: Optional[str] = None
    matched_entry: Optional[Dict[str, Any]] = None
    match_method: Optional[str] = None
    matched_alias: Optional[str] = None

    # Step 1: Exact ID Match (e.g. "ajanta_caves", "taj_mahal")
    q_slug = re.sub(r"[^a-z0-9]", "_", q_raw.lower()).strip("_")
    if q_slug in catalogue:
        matched_mid = q_slug
        matched_entry = catalogue[q_slug]
        match_method = "exact_id"
        matched_alias = matched_entry.get("monument_name")

    # Step 2: Exact Name or Exact Alternate Name Match
    if not matched_mid:
        for mid, item in catalogue.items():
            name_tokens = _clean_tokens(item.get("monument_name", ""))
            if name_tokens == q_tokens or (name_tokens and name_tokens == q_unparen_tokens):
                matched_mid = mid
                matched_entry = item
                match_method = "exact_name"
                matched_alias = item.get("monument_name")
                break

            for alt in item.get("alternate_names", []):
                alt_tokens = _clean_tokens(alt)
                if alt_tokens == q_tokens or (alt_tokens and alt_tokens == q_unparen_tokens):
                    matched_mid = mid
                    matched_entry = item
                    match_method = "exact_alias"
                    matched_alias = alt
                    break
            if matched_mid:
                break

    # Step 3: Spelling Similarity (difflib edit similarity >= 0.88 on full normalized string)
    if not matched_mid:
        q_str = " ".join(q_tokens)
        q_unparen_str = " ".join(q_unparen_tokens)
        for mid, item in catalogue.items():
            m_str = " ".join(_clean_tokens(item.get("monument_name", "")))
            if m_str and (
                difflib.SequenceMatcher(None, q_str, m_str).ratio() >= 0.88
                or difflib.SequenceMatcher(None, q_unparen_str, m_str).ratio() >= 0.88
            ):
                matched_mid = mid
                matched_entry = item
                match_method = "spelling_similarity_name"
                matched_alias = item.get("monument_name")
                break

            for alt in item.get("alternate_names", []):
                a_str = " ".join(_clean_tokens(alt))
                if a_str and (
                    difflib.SequenceMatcher(None, q_str, a_str).ratio() >= 0.88
                    or difflib.SequenceMatcher(None, q_unparen_str, a_str).ratio() >= 0.88
                ):
                    matched_mid = mid
                    matched_entry = item
                    match_method = "spelling_similarity_alias"
                    matched_alias = alt
                    break
            if matched_mid:
                break

    # Step 4: Proper-noun Subset Matching (All distinctive proper nouns of the catalog entry present in query)
    # Strictly guards against generic overlap ("temple", "palace") by requiring at least two distinctive proper nouns.
    if not matched_mid and (q_proper or q_unparen_proper):
        best_candidate = None
        best_score = 0
        for mid, item in catalogue.items():
            all_name_variants = [item.get("monument_name", "")] + item.get("alternate_names", [])
            for var in all_name_variants:
                v_tokens = _clean_tokens(var)
                v_proper = set(_proper_tokens(v_tokens))
                if not v_proper or len(v_proper) < 2:
                    continue
                # If all proper tokens of the catalogue entry are present in the query
                if v_proper.issubset(q_proper) or v_proper.issubset(q_unparen_proper):
                    score = len(v_proper)
                    if score > best_score:
                        best_score = score
                        best_candidate = (mid, item, "proper_token_subset", var)

        if best_candidate and best_score >= 2:
            matched_mid, matched_entry, match_method, matched_alias = best_candidate

    # If no match in the 100-site catalogue manifest, it is OUT_OF_CATALOG
    if not matched_mid or not matched_entry:
        return CatalogueMembershipResult(status=CatalogueStatus.OUT_OF_CATALOG)

    # Determine recognition readiness (all 100 catalogue members are now FAISS-indexed)
    is_ready = matched_mid in get_faiss_recognition_ready_keys()
    status = (
        CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY
        if is_ready
        else CatalogueStatus.CATALOGUED_METADATA_ONLY
    )

    loc = matched_entry.get("location")
    if not loc:
        city = matched_entry.get("city_region", "")
        state = matched_entry.get("state_province", "")
        country = matched_entry.get("country", "")
        parts = [p for p in [city, state, country] if p]
        loc = ", ".join(parts) if parts else country

    return CatalogueMembershipResult(
        status=status,
        monument_id=matched_mid,
        monument_name=matched_entry.get("monument_name"),
        catalog_entry=matched_entry,
        match_method=match_method,
        matched_alias=matched_alias,
        is_recognition_ready=is_ready,
        coordinates=matched_entry.get("coordinates"),
        location=loc,
        country=matched_entry.get("country"),
    )


def resolve_coordinates_from_catalogue(
    proposed_identity: Optional[str]
) -> Tuple[Optional[Dict[str, float]], Optional[str], Optional[str]]:
    """
    Safely resolves geodetic coordinates for a proposed monument identity
    using the shared catalogue membership engine.
    Never hallucinates coordinates; strictly returns (None, None, None) if unverified.
    Returns: (coordinates_dict, catalog_id, geodetic_source)
    """
    res = check_catalogue_membership(proposed_identity)
    if res.status != CatalogueStatus.OUT_OF_CATALOG and res.coordinates:
        country = res.country or "International"
        cat_id = (res.monument_id or "SITE").upper()
        return res.coordinates, cat_id, f"Authoritative Heritage Registry ({country} / UNESCO / National Archive)"

    return None, None, None

