import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin,
  Landmark,
  Clock,
  Layers,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Sliders,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
  BookOpen,
  FileText,
  Scroll,
  Building2,
  HelpCircle,
  Compass,
  Info,
  Navigation
} from 'lucide-react';
import MonumentMap from './MonumentMap';
import PipelineInspector from './PipelineInspector';
import GroundedKnowledgeViewer from './GroundedKnowledgeViewer';

export default function MonographResult({ result, imagePreview, onReset }) {
  const [showInspector, setShowInspector] = useState(true);
  const [showCitations, setShowCitations] = useState(true);

  if (!result) return null;

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

  const isTier1 = verification_tier?.includes('TIER 1');
  const isTier2 = verification_tier?.includes('TIER 2');

  const top1Cand = uncertainty?.top_candidates?.[0] || pipeline_telemetry?.top_3_candidates?.[0];
  const top2Cand = uncertainty?.top_candidates?.[1] || pipeline_telemetry?.top_3_candidates?.[1];
  const gatekeeperPct = Math.round(
    ((uncertainty?.gatekeeper_score ?? pipeline_telemetry?.architectural_gatekeeper_score) || 0) * 100
  );
  const similarityMargin = uncertainty?.similarity_margin ?? 0.0;
  const marginThreshold = uncertainty?.margin_threshold ?? pipeline_telemetry?.margin_threshold ?? 0.08;
  const calibStatus = uncertainty?.calibration_status || 'UNCALIBRATED';

  // =========================================================================
  // VIEW 1: UNCERTAIN MATCH (CLOSE CANDIDATE COMPETITION)
  // =========================================================================
  if (verification_status === 'UNCERTAIN_MATCH') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="space-y-6"
      >
        <div className="bg-archive-ivory border border-amber-300 rounded shadow-plate p-6 sm:p-10">
          {/* Header Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-amber-200 gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-amber-50 text-amber-900 border border-amber-300 font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                UNCERTAIN MATCH // CLOSE CANDIDATE COMPETITION
              </span>
              <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-white text-amber-800 border border-amber-200">
                FLAGGED FOR CURATORIAL OVERSIGHT
              </span>
            </div>

            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-mono text-xs uppercase tracking-wider transition-colors shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5 text-archive-terracotta" />
              <span>Verify Another Specimen</span>
            </motion.button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mt-6">
            {/* Left: Specimen Plate */}
            <div className="md:col-span-5">
              <div className="bg-archive-alabaster border border-archive-hairline p-3 rounded shadow-inner">
                <img
                  src={imagePreview}
                  alt="Uncertain specimen"
                  className="w-full h-72 object-cover rounded filter contrast-105"
                />
                <div className="mt-2.5 text-center font-mono text-[11px] text-archive-muted flex items-center justify-between px-1">
                  <span>FIG 00-C. COMPETING CANDIDATES</span>
                  <span className="font-bold text-amber-800">{exception_id || 'EXC-PENDING'}</span>
                </div>
              </div>
            </div>

            {/* Right: Competing Candidates Breakdown */}
            <div className="md:col-span-7 flex flex-col justify-between space-y-5">
              <div>
                <div className="flex items-center gap-2 text-amber-950 font-serif text-2xl sm:text-3xl font-bold">
                  <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0" />
                  <span>Ambiguous Heritage Attribution</span>
                </div>

                <div className="mt-3 text-sm text-archive-stone leading-relaxed bg-amber-50/70 p-4 rounded border border-amber-200/80 font-sans">
                  {rejection_message ||
                    'Multiple cataloged monuments exhibit strong visual similarity with a narrow margin. To ensure historical integrity, the platform refrains from forcing a single attribution.'}
                </div>

                {/* Side-by-Side Candidates Comparison */}
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                  <div className="bg-white border border-archive-terracotta/60 p-3.5 rounded shadow-sm">
                    <span className="text-[10px] text-archive-terracotta uppercase font-bold block">Top Candidate #1</span>
                    <span className="font-serif font-bold text-base text-archive-charcoal block mt-0.5 truncate">
                      {top1Cand?.monument_name || 'Candidate 1'}
                    </span>
                    <div className="mt-1 flex justify-between text-archive-stone">
                      <span>Cosine Alignment:</span>
                      <span className="font-bold text-archive-charcoal">
                        {((top1Cand?.max_similarity ?? top1Cand?.cosine_similarity ?? 0) * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  <div className="bg-white border border-archive-hairline p-3.5 rounded shadow-sm">
                    <span className="text-[10px] text-archive-stone uppercase font-bold block">Top Candidate #2</span>
                    <span className="font-serif font-bold text-base text-archive-charcoal block mt-0.5 truncate">
                      {top2Cand?.monument_name || 'Candidate 2'}
                    </span>
                    <div className="mt-1 flex justify-between text-archive-stone">
                      <span>Cosine Alignment:</span>
                      <span className="font-bold text-archive-charcoal">
                        {((top2Cand?.max_similarity ?? top2Cand?.cosine_similarity ?? 0) * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Separation Margin Notice */}
                <div className="mt-3 bg-amber-50/80 border border-amber-200 rounded p-3 font-mono text-xs flex justify-between items-center">
                  <span className="text-amber-900">DISCRIMINATIVE GAP:</span>
                  <span className="font-bold text-amber-900">
                    +{similarityMargin.toFixed(4)} (Threshold: {marginThreshold.toFixed(4)})
                  </span>
                </div>
              </div>

              <div className="pt-2 flex flex-col sm:flex-row gap-3">
                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowInspector(!showInspector)}
                  className="flex-1 py-2.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline text-xs font-mono uppercase tracking-wider rounded transition-colors flex items-center justify-center gap-2"
                >
                  <Sliders className="w-4 h-4 text-archive-terracotta" />
                  <span>{showInspector ? 'Hide Telemetry' : 'Inspect Multimodal Telemetry'}</span>
                </motion.button>

                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onReset}
                  className="flex-1 py-2.5 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow transition-colors flex items-center justify-center gap-2"
                >
                  <RotateCcw className="w-4 h-4 text-archive-parchment" />
                  <span>Deposit New Photograph</span>
                </motion.button>
              </div>
            </div>
          </div>
        </div>

        {/* Telemetry Inspector */}
        <AnimatePresence>
          {showInspector && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
            >
              <PipelineInspector
                telemetry={pipeline_telemetry}
                verificationTier={verification_tier}
                confidenceScore={confidence_score}
                uncertainty={uncertainty}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }

  // =========================================================================
  // VIEW 2: UNKNOWN HERITAGE SPECIMEN (UNINDEXED / OUT-OF-CATALOG / METADATA ONLY)
  // =========================================================================
  if (verification_status === 'UNKNOWN_HERITAGE_SPECIMEN') {
    const statusVal =
      result?.catalogue_status ||
      (result?.out_of_catalog_identified
        ? 'OUT_OF_CATALOG'
        : (tier2_analysis?.catalogue_status || (verification_tier?.includes('METADATA ONLY') ? 'CATALOGUED_METADATA_ONLY' : 'OUT_OF_CATALOG')));

    const isMetadataOnly = statusVal === 'CATALOGUED_METADATA_ONLY';
    const isOutOfCatalog = (statusVal === 'OUT_OF_CATALOG' || result?.out_of_catalog_identified) && (result?.out_of_catalog_identified || !!tier2_analysis?.proposed_identity);
    const isUnindexedSpecimen = !isMetadataOnly && !isOutOfCatalog;

    const proposedIdentity =
      monument_name || tier2_analysis?.proposed_identity || 'Unindexed Heritage Specimen';
    const proposedLocation = location || tier2_analysis?.proposed_location || 'Unknown Location';
    const architecturalEvidence =
      tier2_analysis?.visible_architectural_evidence ||
      historical_summary ||
      (structural_features_detected && structural_features_detected.length > 0
        ? structural_features_detected.join(' • ')
        : 'Visual architectural signatures verified by neural feature extraction.');
    const distinguishingFeatures =
      tier2_analysis?.distinguishing_features || structural_features_detected || [];
    const qualitativeConfidence = tier2_analysis?.qualitative_confidence || 'HIGH';
    const modelUsed =
      tier2_analysis?.model_name ||
      (pipeline_telemetry?.gemini_tier2_model || 'gemini-3.1-flash-lite');
    const isOffline = tier2_analysis?.is_offline_fallback ?? false;

    return (
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="space-y-6"
      >
        <div className={`bg-archive-ivory border ${
          isMetadataOnly ? 'border-amber-300' : (isOutOfCatalog ? 'border-slate-300' : 'border-slate-300')
        } rounded shadow-plate p-6 sm:p-10`}>
          <div className={`flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b ${
            isMetadataOnly ? 'border-amber-200' : (isOutOfCatalog ? 'border-slate-200' : 'border-slate-200')
          } gap-3`}>
            <div className="flex flex-wrap items-center gap-2">
              {isMetadataOnly ? (
                <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-amber-50 text-amber-900 border border-amber-300 font-bold flex items-center gap-1.5 shadow-xs">
                  <BookOpen className="w-3.5 h-3.5 text-amber-700" />
                  CATALOGUED — METADATA ONLY
                </span>
              ) : isOutOfCatalog ? (
                <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-slate-100 text-slate-800 border border-slate-300 font-bold flex items-center gap-1.5 shadow-xs">
                  <Compass className="w-3.5 h-3.5 text-slate-700" />
                  OUT-OF-CATALOG HERITAGE IDENTIFIED
                </span>
              ) : (
                <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-slate-100 text-slate-800 border border-slate-300 font-bold flex items-center gap-1.5 shadow-xs">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-700" />
                  EXPLICIT UNCERTAINTY // UNINDEXED HERITAGE SPECIMEN
                </span>
              )}
              <span className={`font-mono text-[10px] uppercase px-2 py-0.5 rounded ${isOffline ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-emerald-50 text-emerald-800 border-emerald-200'} border flex items-center gap-1.5`}>
                <span className={`w-1.5 h-1.5 rounded-full ${isOffline ? 'bg-amber-600' : 'bg-emerald-600'}`}></span>
                {isOffline ? 'OFFLINE FALLBACK' : `ADJUDICATION // ${modelUsed.toUpperCase()}`}
              </span>
            </div>

            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-mono text-xs uppercase tracking-wider transition-colors shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5 text-archive-terracotta" />
              <span>Verify Another Specimen</span>
            </motion.button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mt-6">
            <div className="md:col-span-5">
              <div className="bg-archive-alabaster border border-archive-hairline p-3 rounded shadow-inner">
                <img
                  src={imagePreview}
                  alt="Heritage specimen"
                  className="w-full h-72 object-cover rounded filter contrast-105"
                />
                <div className="mt-2.5 text-center font-mono text-[11px] text-archive-muted flex items-center justify-between px-1">
                  <span>
                    {isMetadataOnly
                      ? 'FIG 00-CAT. CATALOGUED SPECIMEN (METADATA VERIFIED)'
                      : (isOutOfCatalog ? 'FIG 00-OOC. OPEN-WORLD SPECIMEN' : 'FIG 00-U. UNINDEXED MONUMENT')}
                  </span>
                  <span className="font-bold text-sky-800">{exception_id || 'EXC-PENDING'}</span>
                </div>
              </div>
            </div>

            <div className="md:col-span-7 flex flex-col justify-between space-y-5">
              <div>
                <div className="flex items-center gap-2 text-archive-charcoal font-serif text-2xl sm:text-3xl font-bold">
                  {isMetadataOnly ? (
                    <BookOpen className="w-6 h-6 text-amber-700 flex-shrink-0" />
                  ) : isOutOfCatalog ? (
                    <Compass className="w-6 h-6 text-sky-600 flex-shrink-0" />
                  ) : (
                    <ShieldAlert className="w-6 h-6 text-slate-600 flex-shrink-0" />
                  )}
                  <span>{(isMetadataOnly || isOutOfCatalog) ? proposedIdentity : 'Unindexed Heritage Site Detected'}</span>
                </div>

                {(isMetadataOnly || isOutOfCatalog) && proposedLocation && (
                  <div className="flex items-center gap-1.5 text-xs font-mono text-archive-stone mt-1">
                    <MapPin className="w-3.5 h-3.5 text-archive-terracotta" />
                    <span>{proposedLocation}</span>
                    <span className="text-archive-muted font-normal">• Confidence: <strong className="text-sky-800 uppercase">{qualitativeConfidence}</strong></span>
                  </div>
                )}

                <div className={`mt-3 text-sm leading-relaxed ${
                  isMetadataOnly
                    ? 'bg-amber-50/70 border-amber-200/80 text-amber-950'
                    : (isOutOfCatalog ? 'bg-sky-50/70 border-sky-200/80 text-slate-800' : 'bg-slate-50/70 border-slate-200/80 text-archive-stone')
                } p-4 rounded border font-sans`}>
                  {architecturalEvidence}
                </div>

                {/* Distinguishing Features Chips */}
                {(isMetadataOnly || isOutOfCatalog) && distinguishingFeatures.length > 0 && (
                  <div className="mt-3">
                    <div className="text-[10px] font-mono uppercase text-archive-stone tracking-wider font-bold mb-1.5">
                      Identified Architectural Indicators:
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {distinguishingFeatures.map((feat, idx) => (
                        <span
                          key={idx}
                          className={`px-2 py-0.5 bg-white border ${
                            isMetadataOnly ? 'border-amber-200 text-amber-950' : 'border-sky-200 text-sky-950'
                          } font-mono text-[11px] rounded shadow-xs`}
                        >
                          {feat}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Original Catalog Competition Diagnostics */}
                <div className="mt-4 bg-white border border-archive-hairline rounded p-4 font-mono text-xs space-y-2">
                  <div className="flex justify-between items-center pb-2 border-b border-archive-parchment">
                    <span className="text-archive-muted uppercase tracking-wider text-[10px]">
                      CURATORIAL RECORD TICKET:
                    </span>
                    <span className="font-bold text-archive-terracotta">{exception_id || 'LOGGED'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-archive-stone">GATEKEEPER SCORE:</span>
                    <span className="font-bold text-emerald-800">{gatekeeperPct}% Monument Signature</span>
                  </div>
                  {top1Cand && (
                    <div className="flex justify-between">
                      <span className="text-archive-stone">NEAREST IN-CATALOG CANDIDATE:</span>
                      <span className="font-semibold text-archive-charcoal">
                        {top1Cand.monument_name} ({((top1Cand.max_similarity ?? top1Cand.cosine_similarity ?? 0) * 100).toFixed(1)}% Sim)
                      </span>
                    </div>
                  )}
                  {top2Cand && (
                    <div className="flex justify-between text-archive-muted text-[11px]">
                      <span>RUNNER-UP IN-CATALOG CANDIDATE:</span>
                      <span>{top2Cand.monument_name} ({((top2Cand.max_similarity ?? top2Cand.cosine_similarity ?? 0) * 100).toFixed(1)}% Sim)</span>
                    </div>
                  )}
                  <div className="flex justify-between pt-1 border-t border-archive-parchment">
                    <span className="text-archive-stone">DECISION ATTRIBUTION:</span>
                    <span className="text-sky-900 font-semibold">
                      {isMetadataOnly
                        ? 'CATALOGUED MONUMENT // METADATA VERIFIED (TIER-2 GROUNDED)'
                        : isOutOfCatalog
                        ? 'OUT-OF-CATALOG HERITAGE IDENTIFIED (CATALOGUE EXPANSION RECOMMENDED)'
                        : 'HONEST RETRIEVAL // NO FORCED ATTRIBUTION'}
                    </span>
                  </div>
                </div>

                {isMetadataOnly ? (
                  <p className="mt-2 text-[11px] font-sans italic text-archive-stone leading-tight">
                    * Note: This monument belongs to the 100-site canonical catalogue (Metadata Verified). Visual identification provided by Gemini 3.1 Flash-Lite (Tier 1 FAISS vector anchors pending photographic field survey; not falsely attributed via vector index).
                  </p>
                ) : isOutOfCatalog ? (
                  <p className="mt-2 text-[11px] font-sans italic text-archive-stone leading-tight">
                    * Note: This structure lies outside the canonical 100-site catalogue. Attribution has been adjudicated by Gemini 3.1 Flash-Lite based on authentic architectural features.
                  </p>
                ) : null}
              </div>

              <div className="pt-2 flex flex-col sm:flex-row gap-3">
                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowInspector(!showInspector)}
                  className="flex-1 py-2.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline text-xs font-mono uppercase tracking-wider rounded transition-colors flex items-center justify-center gap-2"
                >
                  <Sliders className="w-4 h-4 text-archive-terracotta" />
                  <span>{showInspector ? 'Hide Telemetry' : 'Inspect Telemetry'}</span>
                </motion.button>

                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onReset}
                  className="flex-1 py-2.5 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow transition-colors flex items-center justify-center gap-2"
                >
                  <RotateCcw className="w-4 h-4 text-archive-parchment" />
                  <span>Deposit New Photograph</span>
                </motion.button>
              </div>
            </div>
          </div>

          {/* Geographical Map Panel for Gemini Adjudication */}
          <div className="mt-8 pt-6 border-t border-archive-hairline">
            <div className="flex items-center justify-between mb-3 font-mono text-xs text-archive-charcoal">
              <div className="flex items-center gap-1.5 font-semibold text-sky-900">
                <Navigation className="w-3.5 h-3.5 text-sky-700" />
                <span>GEODETIC CARTOGRAPHY // OPEN-WORLD GEOGRAPHIC MAPPING</span>
              </div>
              <span className="text-[11px] text-archive-stone">
                {tier2_analysis?.geodetic_source || 'Authoritative Heritage Registry (UNESCO/ASI)'}
              </span>
            </div>
            {(coordinates || tier2_analysis?.verified_coordinates) ? (
              <MonumentMap
                coordinates={coordinates || tier2_analysis?.verified_coordinates}
                monumentName={proposedIdentity}
                location={proposedLocation}
                catalogId={catalog_id || tier2_analysis?.catalog_id || 'OPEN-WORLD-SITE'}
              />
            ) : (
              <div className="bg-archive-alabaster border border-dashed border-archive-hairline rounded p-6 flex flex-col items-center justify-center text-center font-mono text-xs text-archive-muted space-y-1.5">
                <MapPin className="w-5 h-5 text-archive-stone/60" />
                <span className="text-archive-stone font-semibold">
                  Verified geographical coordinates unavailable for this site; curatorial geodetic audit pending.
                </span>
                <span className="text-[11px] text-archive-muted">
                  Spatial boundaries and geodetic reference are pending ingestion into the 100-site heritage register.
                </span>
              </div>
            )}
          </div>
        </div>

        <AnimatePresence>
          {showInspector && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
            >
              <PipelineInspector
                telemetry={pipeline_telemetry}
                verificationTier={verification_tier}
                confidenceScore={confidence_score}
                uncertainty={uncertainty}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }

  // =========================================================================
  // VIEW 3: REVIEW REQUIRED (GEODETIC CONFLICT OR DEGRADED SPECIMEN)
  // =========================================================================
  if (verification_status === 'REVIEW_REQUIRED') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="space-y-6"
      >
        <div className="bg-archive-ivory border border-rose-300 rounded shadow-plate p-6 sm:p-10">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-rose-200 gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-rose-50 text-rose-900 border border-rose-200 font-bold flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-700" />
                CURATORIAL AUDIT REQUIRED // EVIDENCE CONFLICT OR QUALITY DEGRADATION
              </span>
            </div>

            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-mono text-xs uppercase tracking-wider transition-colors shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5 text-archive-terracotta" />
              <span>Verify Another Specimen</span>
            </motion.button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mt-6">
            <div className="md:col-span-5">
              <div className="bg-archive-alabaster border border-archive-hairline p-3 rounded shadow-inner">
                <img
                  src={imagePreview}
                  alt="Review required specimen"
                  className="w-full h-72 object-cover rounded filter contrast-105"
                />
                <div className="mt-2.5 text-center font-mono text-[11px] text-archive-muted flex items-center justify-between px-1">
                  <span>FIG 00-R. AUDIT SPECIMEN</span>
                  <span className="font-bold text-rose-800">{exception_id || 'EXC-PENDING'}</span>
                </div>
              </div>
            </div>

            <div className="md:col-span-7 flex flex-col justify-between space-y-5">
              <div>
                <div className="flex items-center gap-2 text-rose-950 font-serif text-2xl sm:text-3xl font-bold">
                  <ShieldAlert className="w-6 h-6 text-rose-600 flex-shrink-0" />
                  <span>Curatorial Verification Interrupted</span>
                </div>

                <div className="mt-3 text-sm text-archive-stone leading-relaxed bg-rose-50/70 p-4 rounded border border-rose-200/80 font-sans">
                  {rejection_message ||
                    'An evidence anomaly (geodetic coordinates conflict, severe blur, or exposure degradation) was caught by the Uncertainty Engine. Manual curator audit is required before registration.'}
                </div>

                <div className="mt-4 bg-white border border-rose-200 rounded p-4 font-mono text-xs space-y-2">
                  <div className="flex justify-between items-center pb-2 border-b border-rose-100">
                    <span className="text-archive-muted uppercase tracking-wider text-[10px]">
                      EXCEPTION AUDIT TICKET:
                    </span>
                    <span className="font-bold text-rose-800">{exception_id || 'QUEUED'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-archive-stone">CLOSEST CANDIDATE:</span>
                    <span className="font-semibold text-archive-charcoal">
                      {top1Cand?.monument_name || 'None'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-archive-stone">GPS SENSOR STATUS:</span>
                    <span className="text-rose-800 font-semibold">
                      {uncertainty?.gps_evidence?.note || 'Sensor check active'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-2 flex flex-col sm:flex-row gap-3">
                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowInspector(!showInspector)}
                  className="flex-1 py-2.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline text-xs font-mono uppercase tracking-wider rounded transition-colors flex items-center justify-center gap-2"
                >
                  <Sliders className="w-4 h-4 text-archive-terracotta" />
                  <span>{showInspector ? 'Hide Telemetry' : 'Inspect Audit Telemetry'}</span>
                </motion.button>

                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onReset}
                  className="flex-1 py-2.5 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow transition-colors flex items-center justify-center gap-2"
                >
                  <RotateCcw className="w-4 h-4 text-archive-parchment" />
                  <span>Deposit New Photograph</span>
                </motion.button>
              </div>
            </div>
          </div>
        </div>

        <AnimatePresence>
          {showInspector && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
            >
              <PipelineInspector
                telemetry={pipeline_telemetry}
                verificationTier={verification_tier}
                confidenceScore={confidence_score}
                uncertainty={uncertainty}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }

  // =========================================================================
  // VIEW 4: NON-MONUMENT REJECTION
  // =========================================================================
  if (!is_monument || verification_status === 'NON_MONUMENT_REJECTED') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="space-y-6"
      >
        <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-6 sm:p-10">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-archive-hairline gap-3">
            <span className="archival-stamp-rejected">
              SPECIMEN REJECTED // NON-HERITAGE
            </span>
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-mono text-xs uppercase tracking-wider transition-colors shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5 text-archive-terracotta" />
              <span>Verify Another Specimen</span>
            </motion.button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mt-6">
            <div className="md:col-span-5">
              <div className="bg-archive-alabaster border border-archive-hairline p-3 rounded shadow-inner">
                <img
                  src={imagePreview}
                  alt="Rejected specimen"
                  className="w-full h-64 object-cover rounded filter contrast-105"
                />
                <div className="mt-2 text-center font-mono text-[11px] text-archive-muted">
                  FIG 00. REJECTED DEPOSIT SPECIMEN
                </div>
              </div>
            </div>

            <div className="md:col-span-7 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-rose-900 font-serif text-2xl sm:text-3xl font-bold">
                  <AlertTriangle className="w-6 h-6 text-rose-600 flex-shrink-0" />
                  <span>Archival Verification Disapproved</span>
                </div>

                <p className="mt-3 text-sm text-archive-stone leading-relaxed bg-rose-50/70 p-4 rounded border border-rose-200/70 font-sans">
                  {rejection_message || "The deposited specimen does not exhibit structural motifs or historic features associated with registered Indian monuments or UNESCO heritage landmarks."}
                </p>

                <div className="mt-4 space-y-2 text-xs font-mono text-archive-stone bg-archive-alabaster/80 p-3.5 rounded border border-archive-hairline">
                  <div className="flex justify-between">
                    <span>ARCHITECTURAL PROBABILITY:</span>
                    <span className="font-bold text-rose-700">{gatekeeperPct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>TOP VECTOR COSINE SIMILARITY:</span>
                    <span>
                      {((top1Cand?.max_similarity ?? top1Cand?.cosine_similarity ?? 0)).toFixed(4)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>DECISION ROUTING:</span>
                    <span>ROUTE 3 // CURATORIAL REJECTION GATEWAY</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-archive-hairline">
                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onReset}
                  className="w-full py-2.5 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow transition-colors flex items-center justify-center gap-2"
                >
                  <RotateCcw className="w-4 h-4 text-archive-parchment" />
                  <span>Deposit New Photograph</span>
                </motion.button>
              </div>
            </div>
          </div>
        </div>

        <PipelineInspector
          telemetry={pipeline_telemetry}
          verificationTier={verification_tier}
          confidenceScore={confidence_score}
          uncertainty={uncertainty}
        />
      </motion.div>
    );
  }

  // =========================================================================
  // VIEW 5: VERIFIED MONUMENT MONOGRAPH
  // =========================================================================
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
      className="space-y-8"
    >
      {/* Top Banner & Control Ribbon */}
      <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-6 sm:p-8">
        
        {/* Archival Inked Accession Ribbon */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 double-border-bottom gap-4">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-emerald-50 text-emerald-900 border border-emerald-300 font-bold flex items-center gap-1.5 shadow-xs">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
              <span>CATALOGUED MONUMENT</span>
            </span>
            <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-white text-archive-charcoal border border-archive-hairline font-bold">
              {catalog_id || 'ASI-ARCH-REG'}
            </span>
            <span className={isTier1 ? "archival-stamp" : "archival-stamp-tier2"}>
              <ShieldCheck className="w-3 h-3" />
              <span>{isTier1 ? 'TIER 1 • VECTOR RETRIEVAL' : 'TIER 2 • VLM ADJUDICATED'}</span>
            </span>
            <span className="font-mono text-[11px] text-archive-stone px-2 py-0.5 rounded bg-archive-parchment border border-archive-hairline">
              ALIGNMENT: {((top1Cand?.max_similarity ?? (confidence_score / 100)) || 0).toFixed(4)}
            </span>
            {preservation_status && (
              <span className="font-mono text-[10px] bg-archive-alabaster text-archive-stone border border-archive-hairline px-2 py-0.5 rounded font-medium flex items-center gap-1">
                PROTECTED MONUMENT
              </span>
            )}
          </div>

          <div className="flex items-center gap-2.5 self-start md:self-auto flex-shrink-0">
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowInspector(!showInspector)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-mono text-xs uppercase tracking-wider transition-colors shadow-xs"
            >
              <Sliders className="w-3.5 h-3.5 text-archive-terracotta" />
              <span>{showInspector ? 'Hide Telemetry' : 'Inspect Telemetry'}</span>
              {showInspector ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </motion.button>

            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-archive-charcoal hover:bg-black text-white rounded font-mono text-xs uppercase tracking-wider transition-colors shadow-xs"
            >
              <RotateCcw className="w-3.5 h-3.5 text-archive-parchment" />
              <span>New Search</span>
            </motion.button>
          </div>
        </div>

        {/* Monograph Core Split Layout (Asymmetric 5/7) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-6">
          
          {/* Left Column: Specimen Plate Container & Cartography */}
          <div className="lg:col-span-5 space-y-5">
            <div className="bg-archive-alabaster border border-archive-hairline p-3 rounded shadow-inner">
              <div className="relative overflow-hidden rounded border border-archive-hairline/80 bg-black/5">
                <img
                  src={imagePreview}
                  alt={monument_name}
                  className="w-full h-80 object-cover filter contrast-105"
                />
                <div className="absolute bottom-2 right-2 bg-archive-charcoal/80 text-white font-mono text-[10px] px-2 py-0.5 rounded backdrop-blur-sm">
                  {catalog_id}
                </div>
              </div>
              <div className="mt-2.5 px-1 flex items-center justify-between text-[11px] font-mono text-archive-stone">
                <span>FIG 01. UPLOADED SPECIMEN</span>
                <span className="font-semibold text-archive-terracotta">
                  {uncertainty?.gps_evidence?.geo_boost_applied ? 'EXIF GPS VERIFIED' : 'CLIP VECTOR VERIFIED'}
                </span>
              </div>
            </div>

            {/* Embedded Geodetic Map */}
            {coordinates && (
              <MonumentMap
                coordinates={coordinates}
                monumentName={monument_name}
                catalogId={catalog_id}
                location={location}
              />
            )}
          </div>

          {/* Right Column: Historical Dossier */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
            <div>
              {/* Header Titles */}
              <div className="border-b border-archive-hairline/80 pb-4">
                <div className="font-mono text-[11px] text-archive-terracotta tracking-stamp uppercase font-bold">
                  OFFICIAL ARCHIVAL DOSSIER
                </div>
                <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold text-archive-charcoal tracking-tight mt-1">
                  {monument_name}
                </h2>
                <div className="flex items-center gap-1.5 text-sm text-archive-stone mt-2">
                  <MapPin className="w-4 h-4 text-archive-terracotta flex-shrink-0" />
                  <span className="font-medium">{location}</span>
                </div>
              </div>

              {/* Architectural Metadata Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-5">
                <div className="bg-archive-alabaster/70 border border-archive-hairline p-3.5 rounded">
                  <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block">
                    Architectural Style
                  </span>
                  <div className="font-sans font-semibold text-archive-charcoal mt-1 flex items-center gap-1.5">
                    <Landmark className="w-4 h-4 text-archive-terracotta flex-shrink-0" />
                    <span>{architectural_style || 'Heritage Monument'}</span>
                  </div>
                </div>

                <div className="bg-archive-alabaster/70 border border-archive-hairline p-3.5 rounded">
                  <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block">
                    Built By / Historical Era
                  </span>
                  <div className="font-sans font-semibold text-archive-charcoal mt-1 flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-archive-terracotta flex-shrink-0" />
                    <span>{built_by_or_era || 'Historical Era'}</span>
                  </div>
                </div>
              </div>

              {/* Historical Summary */}
              <div className="mt-5">
                <div className="font-mono text-xs uppercase tracking-wider text-archive-stone mb-2 font-semibold">
                  HISTORICAL CURATORIAL MONOGRAPH
                </div>
                <div className="font-serif text-base sm:text-lg text-archive-ink leading-relaxed bg-archive-alabaster/40 p-4 rounded border border-archive-hairline/80">
                  {historical_summary}
                </div>
              </div>

              {/* Structural Features Detected */}
              {structural_features_detected.length > 0 && (
                <div className="mt-5">
                  <div className="font-mono text-xs uppercase tracking-wider text-archive-stone mb-2 font-semibold flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-archive-terracotta" />
                    <span>ARCHITECTURAL SIGNATURES DETECTED</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {structural_features_detected.map((feature, idx) => (
                      <span
                        key={idx}
                        className="font-mono text-xs bg-white border border-archive-hairline px-3 py-1 rounded text-archive-charcoal shadow-sm flex items-center gap-1.5"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-archive-terracotta"></span>
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Curatorial Micro Footer */}
            <div className="mt-4 pt-3 border-t border-archive-hairline flex flex-wrap items-center justify-between text-[11px] font-mono text-archive-muted gap-2">
              <span>REGISTERED IN UNESCO & ASI DATABASE</span>
              <span>TWO-TIER HYBRID ARCHIVAL RECOGNITION</span>
            </div>
          </div>
        </div>

        {/* Grounded Cultural Citations Section */}
        {(grounded_citations || preservation_status) && (
          <div className="mt-8 pt-6 border-t border-archive-hairline">
            <div className="bg-archive-alabaster/60 border border-archive-hairline rounded p-5 sm:p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Scroll className="w-4 h-4 text-archive-terracotta flex-shrink-0" />
                  <h3 className="font-mono text-xs uppercase tracking-stamp text-archive-charcoal font-bold">
                    GROUNDED CULTURAL CITATIONS & STATUTORY CONTEXT
                  </h3>
                </div>
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  className="font-mono text-[11px] text-archive-stone hover:text-archive-charcoal flex items-center gap-1"
                >
                  <span>{showCitations ? 'Collapse Citations' : 'Expand Citations'}</span>
                  {showCitations ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>

              {preservation_status && (
                <div className="bg-white border border-archive-hairline p-3 rounded font-mono text-xs">
                  <span className="text-[10px] text-archive-muted uppercase tracking-wider block mb-0.5">
                    Statutory Preservation Framework
                  </span>
                  <span className="font-medium text-archive-charcoal">
                    {preservation_status}
                  </span>
                </div>
              )}

              {showCitations && grounded_citations && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1 text-xs">
                  {grounded_citations.primary_source && (
                    <div className="bg-white border border-archive-hairline p-3 rounded space-y-1">
                      <span className="font-mono text-[10px] uppercase text-archive-terracotta font-semibold block">
                        Primary Source Archive
                      </span>
                      <p className="font-sans text-archive-stone leading-relaxed">
                        {grounded_citations.primary_source}
                      </p>
                    </div>
                  )}

                  {grounded_citations.gazetteer_reference && (
                    <div className="bg-white border border-archive-hairline p-3 rounded space-y-1">
                      <span className="font-mono text-[10px] uppercase text-archive-terracotta font-semibold block">
                        Gazetteer / Survey Record
                      </span>
                      <p className="font-sans text-archive-stone leading-relaxed">
                        {grounded_citations.gazetteer_reference}
                      </p>
                    </div>
                  )}

                  {grounded_citations.unesco_whc_ref && (
                    <div className="bg-white border border-archive-hairline p-3 rounded space-y-1">
                      <span className="font-mono text-[10px] uppercase text-archive-terracotta font-semibold block">
                        UNESCO World Heritage Dossier
                      </span>
                      <p className="font-sans text-archive-stone leading-relaxed">
                        {grounded_citations.unesco_whc_ref}
                      </p>
                    </div>
                  )}

                  {grounded_citations.epigraphical_records && (
                    <div className="bg-white border border-archive-hairline p-3 rounded space-y-1">
                      <span className="font-mono text-[10px] uppercase text-archive-terracotta font-semibold block">
                        Epigraphical Records & Inscriptions
                      </span>
                      <p className="font-sans text-archive-stone leading-relaxed">
                        {grounded_citations.epigraphical_records}
                      </p>
                    </div>
                  )}

                  {grounded_citations.curatorial_notes && (
                    <div className="md:col-span-2 bg-archive-parchment/40 border border-archive-hairline p-3 rounded space-y-1">
                      <span className="font-mono text-[10px] uppercase text-archive-stone font-semibold block">
                        Field Survey & Curatorial Notes
                      </span>
                      <p className="font-sans text-archive-stone leading-relaxed italic">
                        "{grounded_citations.curatorial_notes}"
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Phase 8.0B Local Architectural Evidence & Geometric Verification */}
      {local_features && (
        <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-5 sm:p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-archive-hairline">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-archive-terracotta flex-shrink-0" />
              <h3 className="font-mono text-xs uppercase tracking-stamp text-archive-charcoal font-bold">
                LOCAL ARCHITECTURAL EVIDENCE & GEOMETRIC VERIFICATION (SIH 2025 TIER 1C)
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded font-mono text-[10px] uppercase font-bold tracking-wider border ${
                local_features.alignment_status === 'AGREEMENT_CONFIRMED_GEOMETRIC'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                  : local_features.alignment_status === 'AGREEMENT_CONFIRMED_VISUAL'
                  ? 'bg-teal-50 text-teal-800 border-teal-300'
                  : local_features.alignment_status === 'DIVERGENT_EVIDENCE'
                  ? 'bg-amber-50 text-amber-800 border-amber-300'
                  : 'bg-neutral-50 text-neutral-700 border-neutral-300'
              }`}>
                {local_features.alignment_status || 'LOCAL_ANALYZED'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 pt-1 text-xs font-mono">
            {/* Region Analysis */}
            <div className="bg-archive-alabaster/70 border border-archive-hairline p-3 rounded space-y-1">
              <span className="text-[10px] text-archive-muted uppercase tracking-wider block">
                Region Proposals
              </span>
              <div className="text-sm font-semibold text-archive-charcoal">
                {local_features.regions_evaluated || 0} Architectural Sectors
              </div>
              <p className="text-[10px] text-archive-stone font-sans">
                Multi-scale crown, columns, friezes & saliency
              </p>
            </div>

            {/* Local Candidate Match */}
            <div className="bg-archive-alabaster/70 border border-archive-hairline p-3 rounded space-y-1">
              <span className="text-[10px] text-archive-muted uppercase tracking-wider block">
                Top Local Match
              </span>
              <div className="text-sm font-semibold text-archive-terracotta truncate">
                {local_features.top_local_candidate?.monument_name || 'N/A'}
              </div>
              <div className="text-[10px] text-archive-stone">
                Max Sim: {(local_features.top_local_candidate?.max_similarity || 0).toFixed(4)}
              </div>
            </div>

            {/* Classical SIFT / RANSAC Geometric Verification */}
            <div className="bg-archive-alabaster/70 border border-archive-hairline p-3 rounded space-y-1">
              <span className="text-[10px] text-archive-muted uppercase tracking-wider block">
                SIFT / RANSAC Homography
              </span>
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${
                  local_features.geometric_verification?.status === 'VERIFIED'
                    ? 'bg-emerald-500'
                    : 'bg-amber-400'
                }`} />
                <span className="text-sm font-semibold text-archive-charcoal">
                  {local_features.geometric_verification?.status || 'PENDING'}
                </span>
              </div>
              <div className="text-[10px] text-archive-stone">
                Inliers: {local_features.geometric_verification?.inliers_count || 0} / {local_features.geometric_verification?.good_matches_count || 0} ({((local_features.geometric_verification?.inlier_ratio || 0) * 100).toFixed(1)}%)
              </div>
            </div>
          </div>

          {/* Curatorial Explanation Strip */}
          {local_features.alignment_explanation && (
            <div className="bg-archive-parchment/60 border border-archive-hairline p-3 rounded text-xs font-sans text-archive-stone leading-relaxed">
              <span className="font-mono text-[10px] uppercase font-semibold text-archive-charcoal mr-2">
                ALIGNMENT AUDIT:
              </span>
              {local_features.alignment_explanation}
            </div>
          )}
        </div>
      )}

      {/* Phase 6.3 Grounded Historical Knowledge Engine */}
      {monument_key && (
        <GroundedKnowledgeViewer
          monumentKey={monument_key}
          monumentName={monument_name}
        />
      )}

      {/* Interactive Pipeline Inspector */}
      <AnimatePresence>
        {showInspector && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
          >
            <PipelineInspector
              telemetry={pipeline_telemetry}
              verificationTier={verification_tier}
              confidenceScore={confidence_score}
              uncertainty={uncertainty}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
