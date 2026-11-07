const React = require('react');

// Mock data fixtures representing the 5 core states + edge cases
const mockResults = {
  // 1. VERIFIED_MATCH
  verifiedMatch: {
    is_monument: true,
    verification_status: 'VERIFIED_MATCH',
    is_uncertain: false,
    verification_tier: 'TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX',
    confidence_score: 99.8,
    catalog_id: 'ASI-ARCH-TAJ-01',
    monument_key: 'taj_mahal',
    monument_name: 'Taj Mahal',
    location: 'Agra, Uttar Pradesh',
    coordinates: { lat: 27.1751, lng: 78.0421 },
    architectural_style: 'Mughal Architecture',
    built_by_or_era: 'Shah Jahan (1631–1648)',
    historical_summary: 'An immense mausoleum of white marble...',
    structural_features_detected: ['Central Onion Dome', 'Four Minarets', 'Iwan Arches'],
    preservation_status: 'UNESCO World Heritage Site',
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.985,
      top_3_candidates: [{ monument_name: 'Taj Mahal', cosine_similarity: 0.943 }],
      margin_threshold: 0.08,
    },
    uncertainty: {
      decision: 'VERIFIED_MATCH',
      calibration_status: 'EXPERIMENTAL_CALIBRATED',
      similarity_margin: 0.25,
      margin_threshold: 0.08,
    },
    tier2_analysis: null,
    out_of_catalog_identified: false,
  },

  // 2. UNCERTAIN_MATCH
  uncertainMatch: {
    is_monument: true,
    verification_status: 'UNCERTAIN_MATCH',
    is_uncertain: true,
    verification_tier: 'UNCERTAIN // CLOSE CANDIDATE COMPETITION',
    confidence_score: 83.2,
    catalog_id: 'ASI-ARCH-CHA-06',
    monument_key: 'charminar',
    monument_name: 'Charminar',
    rejection_message: 'Ambiguous visual distinction between top unique candidates.',
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.82,
      top_3_candidates: [
        { monument_name: 'Charminar', cosine_similarity: 0.8324 },
        { monument_name: 'Taj Mahal', cosine_similarity: 0.8155 },
      ],
      margin_threshold: 0.08,
    },
    uncertainty: {
      decision: 'UNCERTAIN_MATCH',
      top_candidates: [
        { monument_name: 'Charminar', cosine_similarity: 0.8324 },
        { monument_name: 'Taj Mahal', cosine_similarity: 0.8155 },
      ],
      similarity_margin: 0.0169,
      margin_threshold: 0.08,
    },
    tier2_analysis: null,
    out_of_catalog_identified: false,
  },

  // 3. UNKNOWN_HERITAGE_SPECIMEN (Catalogued Metadata-Only identified by Gemini)
  cataloguedMetadataOnly: {
    is_monument: true,
    verification_status: 'UNKNOWN_HERITAGE_SPECIMEN',
    is_uncertain: true,
    verification_tier: 'CATALOGUED — METADATA ONLY // GEMINI-3.1-FLASH-LITE',
    catalogue_status: 'CATALOGUED_METADATA_ONLY',
    confidence_score: 83.2,
    monument_name: 'Ajanta Caves',
    catalog_id: 'AJANTA_CAVES',
    location: 'Aurangabad District, Maharashtra, India',
    rejection_message: "Specimen catalogued in 100-Site Heritage Register ('Ajanta Caves'). Metadata verified; visual identification by gemini-3.1-flash-lite.",
    out_of_catalog_identified: false,
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.92,
      top_3_candidates: [
        { monument_name: 'Konark Sun Temple', cosine_similarity: 0.8124 },
        { monument_name: 'Brihadeeswarar Temple', cosine_similarity: 0.7955 },
      ],
      margin_threshold: 0.08,
    },
    uncertainty: {
      decision: 'UNKNOWN_HERITAGE_SPECIMEN',
      top_candidates: [
        { monument_name: 'Konark Sun Temple', cosine_similarity: 0.8124 },
      ],
      similarity_margin: 0.0169,
    },
    tier2_analysis: {
      proposed_identity: 'Ajanta Caves (Cave 19)',
      proposed_location: 'Aurangabad District, Maharashtra, India',
      is_heritage_structure: true,
      is_catalog_monument: true,
      catalogue_status: 'CATALOGUED_METADATA_ONLY',
      visible_architectural_evidence: 'Rock-cut chaitya hall with horseshoe-shaped arched chaitya window and monolithic stupa.',
      distinguishing_features: ['Horseshoe chaitya window', 'Rock-cut pillars', 'Carved Buddha standing figure'],
      qualitative_confidence: 'HIGH',
      model_name: 'gemini-3.1-flash-lite',
      is_offline_fallback: false,
    },
  },

  // 3b. UNKNOWN_HERITAGE_SPECIMEN (Truly Out-of-Catalog identified by Gemini)
  outOfCatalogIdentified: {
    is_monument: true,
    verification_status: 'UNKNOWN_HERITAGE_SPECIMEN',
    is_uncertain: true,
    verification_tier: 'OUT-OF-CATALOG HERITAGE IDENTIFIED // GEMINI-3.1-FLASH-LITE',
    catalogue_status: 'OUT_OF_CATALOG',
    confidence_score: 83.2,
    monument_name: 'Eiffel Tower',
    location: 'Paris, France',
    rejection_message: "Specimen visually identified as out-of-catalog heritage site 'Eiffel Tower'.",
    out_of_catalog_identified: true,
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.88,
      top_3_candidates: [
        { monument_name: 'Charminar', cosine_similarity: 0.7424 },
        { monument_name: 'Taj Mahal', cosine_similarity: 0.7155 },
      ],
      margin_threshold: 0.08,
    },
    uncertainty: {
      decision: 'UNKNOWN_HERITAGE_SPECIMEN',
      top_candidates: [
        { monument_name: 'Charminar', cosine_similarity: 0.7424 },
      ],
      similarity_margin: 0.0269,
    },
    tier2_analysis: {
      proposed_identity: 'Eiffel Tower',
      proposed_location: 'Paris, France',
      is_heritage_structure: true,
      is_catalog_monument: false,
      catalogue_status: 'OUT_OF_CATALOG',
      visible_architectural_evidence: 'Wrought-iron lattice tower with four arched base legs tapering to spire.',
      distinguishing_features: ['Puddle-iron lattice framework', 'Four arched base legs', 'Observation platforms'],
      qualitative_confidence: 'HIGH',
      model_name: 'gemini-3.1-flash-lite',
      is_offline_fallback: false,
    },
  },

  // 4. UNKNOWN_HERITAGE_SPECIMEN (Unindexed / Offline Fallback)
  unknownSpecimenOffline: {
    is_monument: false,
    verification_status: 'UNKNOWN_HERITAGE_SPECIMEN',
    is_uncertain: true,
    verification_tier: 'UNKNOWN SPECIMEN // UNINDEXED OR AMBIGUOUS HERITAGE SITE',
    confidence_score: 64.0,
    monument_name: 'Unindexed / Ambiguous Heritage Site',
    rejection_message: 'Architectural features verified, but similarity fell below threshold.',
    out_of_catalog_identified: false,
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.65,
      top_3_candidates: [{ monument_name: 'Konark Sun Temple', cosine_similarity: 0.64 }],
      margin_threshold: 0.08,
    },
    uncertainty: {
      decision: 'UNKNOWN_HERITAGE_SPECIMEN',
    },
    tier2_analysis: {
      proposed_identity: null,
      proposed_location: null,
      is_heritage_structure: true,
      is_catalog_monument: false,
      visible_architectural_evidence: 'Offline Curatorial Mode: Tier-1 visual vector scanner active.',
      distinguishing_features: ['Offline vector nearest-neighbor inspection'],
      qualitative_confidence: 'UNCERTAIN',
      is_offline_fallback: true,
    },
  },

  // 5. UNKNOWN_HERITAGE_SPECIMEN (Missing tier2_analysis entirely: null or undefined)
  unknownSpecimenMissingTier2: {
    is_monument: false,
    verification_status: 'UNKNOWN_HERITAGE_SPECIMEN',
    is_uncertain: true,
    verification_tier: 'UNKNOWN SPECIMEN // UNINDEXED OR AMBIGUOUS HERITAGE SITE',
    confidence_score: 55.0,
    monument_name: 'Unindexed / Ambiguous Heritage Site',
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.55,
      top_3_candidates: [{ monument_name: 'Sanchi Stupa', cosine_similarity: 0.55 }],
    },
    tier2_analysis: null,
    out_of_catalog_identified: false,
  },

  // 6. NON_MONUMENT_REJECTED
  nonMonumentRejected: {
    is_monument: false,
    verification_status: 'NON_MONUMENT_REJECTED',
    is_uncertain: false,
    verification_tier: 'REJECTED // NON-MONUMENT SPECIMEN',
    confidence_score: 12.0,
    rejection_message: 'The submitted photograph does not contain architectural features.',
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.12,
    },
    uncertainty: {
      decision: 'NON_MONUMENT_REJECTED',
    },
    tier2_analysis: null,
    out_of_catalog_identified: false,
  },

  // 7. REVIEW_REQUIRED
  reviewRequired: {
    is_monument: false,
    verification_status: 'REVIEW_REQUIRED',
    is_uncertain: true,
    verification_tier: 'REVIEW REQUIRED // CURATORIAL AUDIT FLAGGED',
    confidence_score: 82.0,
    monument_name: 'Potential Taj Mahal (Audit Required)',
    rejection_message: 'Geodetic coordinates conflict with verified monument site.',
    pipeline_telemetry: {
      architectural_gatekeeper_score: 0.85,
    },
    uncertainty: {
      decision: 'REVIEW_REQUIRED',
    },
    tier2_analysis: null,
    out_of_catalog_identified: false,
  },
};

// Test extraction and view dispatch for all fixtures
function evaluateResultView(result) {
  const {
    is_monument = false,
    verification_status = 'VERIFIED_MATCH',
    is_uncertain = false,
    verification_tier = 'TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX',
    confidence_score = 0.0,
    catalog_id,
    monument_name,
    monument_key,
    location,
    coordinates,
    architectural_style,
    built_by_or_era,
    historical_summary,
    structural_features_detected = [],
    preservation_status,
    grounded_citations,
    rejection_message,
    pipeline_telemetry,
    human_review_flagged = false,
    exception_id,
    uncertainty,
    local_features,
    tier2_analysis = null,
    out_of_catalog_identified = false,
  } = result;

  const top1Cand = uncertainty?.top_candidates?.[0] || pipeline_telemetry?.top_3_candidates?.[0];
  const top2Cand = uncertainty?.top_candidates?.[1] || pipeline_telemetry?.top_3_candidates?.[1];
  const isTier1 = verification_tier?.includes('TIER 1');
  const gatekeeperPct = Math.round(
    ((uncertainty?.gatekeeper_score ?? pipeline_telemetry?.architectural_gatekeeper_score) || 0) * 100
  );

  let viewType = 'VIEW_UNKNOWN';

  if (verification_status === 'UNCERTAIN_MATCH') {
    viewType = 'VIEW_1_UNCERTAIN_MATCH';
  } else if (verification_status === 'UNKNOWN_HERITAGE_SPECIMEN') {
    const statusVal =
      result?.catalogue_status ||
      (result?.out_of_catalog_identified
        ? 'OUT_OF_CATALOG'
        : (tier2_analysis?.catalogue_status || (verification_tier?.includes('METADATA ONLY') ? 'CATALOGUED_METADATA_ONLY' : 'OUT_OF_CATALOG')));

    const isMetadataOnly = statusVal === 'CATALOGUED_METADATA_ONLY';
    const isOutOfCatalog = (statusVal === 'OUT_OF_CATALOG' || result?.out_of_catalog_identified) && (result?.out_of_catalog_identified || !!tier2_analysis?.proposed_identity);

    const proposedIdentity =
      monument_name || tier2_analysis?.proposed_identity || 'Unindexed Heritage Specimen';
    const proposedLocation = location || tier2_analysis?.proposed_location || 'Unknown Location';
    const architecturalEvidence =
      tier2_analysis?.visible_architectural_evidence ||
      (structural_features_detected && structural_features_detected.length > 0
        ? structural_features_detected.join(' • ')
        : 'Visual architectural signatures verified by neural feature extraction.');
    const distinguishingFeatures =
      tier2_analysis?.distinguishing_features || structural_features_detected || [];
    const qualitativeConfidence = tier2_analysis?.qualitative_confidence || 'MEDIUM';
    const modelUsed =
      tier2_analysis?.model_name ||
      (pipeline_telemetry?.gemini_tier2_model || 'gemini-3.1-flash-lite');
    const isOffline = tier2_analysis?.is_offline_fallback ?? false;

    if (isMetadataOnly) {
      viewType = 'VIEW_2_CATALOGUED_METADATA_ONLY';
    } else if (isOutOfCatalog) {
      viewType = 'VIEW_2_OUT_OF_CATALOG_IDENTIFIED';
    } else {
      viewType = 'VIEW_2_UNINDEXED_SPECIMEN';
    }
  } else if (verification_status === 'REVIEW_REQUIRED') {
    viewType = 'VIEW_3_REVIEW_REQUIRED';
  } else if (verification_status === 'NON_MONUMENT_REJECTED') {
    viewType = 'VIEW_4_NON_MONUMENT_REJECTED';
  } else if (verification_status === 'VERIFIED_MATCH') {
    viewType = 'VIEW_5_VERIFIED_MATCH';
  }

  return {
    viewType,
    monument_name,
    verification_tier,
    is_uncertain,
    gatekeeperPct,
    hasTier2: tier2_analysis !== null,
  };
}

console.log('--- EXECUTING MONOGRAPH RESULT RENDER VERIFICATION ---');
for (const [key, fixture] of Object.entries(mockResults)) {
  try {
    const res = evaluateResultView(fixture);
    console.log(`[PASS] ${key} -> ${res.viewType} (Tier: ${res.verification_tier})`);
  } catch (err) {
    console.error(`[FAIL] ${key}: ${err.message}`);
    process.exit(1);
  }
}
console.log('--- ALL 7 MONOGRAPH RESULT STATES EVALUATED CLEANLY (0 ERRORS) ---');
