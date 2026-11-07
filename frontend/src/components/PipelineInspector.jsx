import React from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Compass,
  Cpu,
  Database,
  GitBranch,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Camera,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';

export default function PipelineInspector({
  telemetry,
  verificationTier,
  confidenceScore,
  uncertainty,
}) {
  if (!telemetry && !uncertainty) return null;

  const {
    exif_gps,
    architectural_gatekeeper_score,
    top_3_candidates = [],
    decision_reason,
    geo_boost_applied,
  } = telemetry || {};

  const gatekeeperPct = Math.round(
    ((uncertainty?.gatekeeper_score ?? architectural_gatekeeper_score) || 0) * 100
  );

  const decision = uncertainty?.decision || 'VERIFIED_MATCH';
  const calibrationStatus = uncertainty?.calibration_status || 'UNCALIBRATED';
  const top1Sim = uncertainty?.top1_similarity ?? (top_3_candidates[0]?.cosine_similarity || 0);
  const top2Sim = uncertainty?.top2_similarity ?? (top_3_candidates[1]?.cosine_similarity || 0);
  const margin = uncertainty?.similarity_margin ?? Math.max(0, top1Sim - top2Sim);
  const marginThreshold = uncertainty?.margin_threshold ?? 0.08;
  const quality = uncertainty?.image_quality;
  const gpsEvidence = uncertainty?.gps_evidence;
  const reasonCodes = uncertainty?.reason_codes || [];
  const requiresReview = uncertainty?.requires_human_review || false;

  const getDecisionBadge = (st) => {
    switch (st) {
      case 'VERIFIED_MATCH':
        return {
          label: 'VERIFIED MATCH',
          color: 'bg-emerald-50 text-emerald-900 border-emerald-300',
          icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />,
        };
      case 'UNCERTAIN_MATCH':
        return {
          label: 'UNCERTAIN MATCH // CLOSE CANDIDATE COMPETITION',
          color: 'bg-amber-100 text-amber-900 border-amber-300',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />,
        };
      case 'UNKNOWN_HERITAGE_SPECIMEN':
        return {
          label: 'UNKNOWN HERITAGE SPECIMEN',
          color: 'bg-amber-50 text-amber-900 border-amber-300',
          icon: <HelpCircle className="w-3.5 h-3.5 text-amber-600" />,
        };
      case 'REVIEW_REQUIRED':
        return {
          label: 'REVIEW REQUIRED // CURATOR AUDIT FLAGGED',
          color: 'bg-rose-50 text-rose-900 border-rose-300',
          icon: <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />,
        };
      default:
        return {
          label: 'NON-MONUMENT REJECTED',
          color: 'bg-rose-100 text-rose-900 border-rose-300',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />,
        };
    }
  };

  const badge = getDecisionBadge(decision);

  return (
    <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-5 sm:p-7 space-y-6">
      
      {/* 1. Header Band */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-archive-hairline gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-archive-terracotta" />
            <h4 className="font-mono text-xs uppercase tracking-stamp text-archive-charcoal font-bold">
              UNCERTAINTY & CONFIDENCE CALIBRATION INSPECTOR
            </h4>
          </div>
          <p className="text-[11px] text-archive-stone font-sans">
            SIH 2025 Multi-Evidence Synthesis: Aggregated FAISS cosine margin, zero-shot gatekeeper, EXIF geodetics, and image quality.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`font-mono text-[10px] uppercase px-2.5 py-1 rounded border font-bold flex items-center gap-1.5 shadow-sm ${badge.color}`}
          >
            {badge.icon}
            <span>{badge.label}</span>
          </span>

          {requiresReview && (
            <span className="font-mono text-[9px] uppercase px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-300 font-semibold animate-pulse">
              HUMAN REVIEW FLAGGED
            </span>
          )}
        </div>
      </div>

      {/* 2. Calibration Invariant Warning Bar */}
      <div className="bg-archive-parchment/60 border border-archive-hairline rounded p-3 text-xs font-mono flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-archive-stone">
          <Info className="w-4 h-4 text-archive-terracotta flex-shrink-0" />
          <span>
            {calibrationStatus === 'UNCALIBRATED' ? (
              <span>
                <strong className="text-archive-charcoal">CALIBRATION STATUS: UNCALIBRATED</strong> — Cosine similarities reflect inner-product vector alignments and are strictly preserved as heuristic evidence, not empirical posterior probabilities.
              </span>
            ) : (
              <span>
                <strong className="text-emerald-800">CALIBRATION STATUS: ACTIVE</strong> — Calibrated probability: {uncertainty?.calibrated_probability ? `${(uncertainty.calibrated_probability * 100).toFixed(1)}%` : 'N/A'}.
              </span>
            )}
          </span>
        </div>
        <span className="font-bold text-[10px] px-2 py-0.5 bg-white border border-archive-hairline rounded text-archive-charcoal flex-shrink-0">
          PROBABILITY MAPPING: {calibrationStatus}
        </span>
      </div>

      {/* 3. Unique-Monument FAISS Margin Visualizer */}
      <div className="bg-white border border-archive-hairline rounded p-4 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-archive-muted">
          <span className="font-semibold text-archive-charcoal flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-archive-terracotta" />
            UNIQUE MONUMENT FAISS RETRIEVAL MARGIN
          </span>
          <span className="text-[10px]">MIN DISCRIMINATIVE GAP: 0.0500</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
          {/* Top 1 */}
          <div className="bg-archive-alabaster/70 border border-archive-hairline p-3 rounded">
            <span className="text-[10px] text-archive-muted uppercase block">Top-1 Unique Candidate</span>
            <div className="font-serif font-bold text-sm text-archive-charcoal mt-0.5 truncate">
              {uncertainty?.top_candidates?.[0]?.monument_name || top_3_candidates[0]?.monument_name || 'None'}
            </div>
            <div className="flex items-center justify-between mt-1 text-[11px]">
              <span className="text-archive-stone">Cosine Similarity:</span>
              <span className="font-bold text-archive-charcoal">{(top1Sim * 100).toFixed(2)}% ({top1Sim.toFixed(4)})</span>
            </div>
          </div>

          {/* Top 2 */}
          <div className="bg-archive-alabaster/70 border border-archive-hairline p-3 rounded">
            <span className="text-[10px] text-archive-muted uppercase block">Top-2 Unique Candidate</span>
            <div className="font-serif font-bold text-sm text-archive-charcoal mt-0.5 truncate">
              {uncertainty?.top_candidates?.[1]?.monument_name || top_3_candidates[1]?.monument_name || 'None'}
            </div>
            <div className="flex items-center justify-between mt-1 text-[11px]">
              <span className="text-archive-stone">Cosine Similarity:</span>
              <span className="font-bold text-archive-charcoal">{(top2Sim * 100).toFixed(2)}% ({top2Sim.toFixed(4)})</span>
            </div>
          </div>

          {/* Margin */}
          <div className={`p-3 rounded border flex flex-col justify-between ${
            margin >= marginThreshold
              ? 'bg-emerald-50/60 border-emerald-200'
              : 'bg-amber-50/60 border-amber-200'
          }`}>
            <div>
              <span className="text-[10px] uppercase block font-semibold text-archive-stone">
                Similarity Margin (Top-1 vs Top-2)
              </span>
              <div className={`font-mono text-lg font-bold mt-0.5 ${
                margin >= marginThreshold ? 'text-emerald-800' : 'text-amber-800'
              }`}>
                +{margin.toFixed(4)}
              </div>
            </div>
            <span className="text-[10px] font-sans text-archive-stone mt-1">
              {margin >= marginThreshold
                ? `Decisive candidate separation (Threshold: ${marginThreshold.toFixed(4)}).`
                : `Narrow margin (Threshold: ${marginThreshold.toFixed(4)}); potential visual ambiguity.`}
            </span>
          </div>
        </div>

        {/* Visual Margin Bar */}
        <div className="space-y-1 pt-1 font-mono text-[10px] text-archive-stone">
          <div className="flex justify-between">
            <span>DISCRIMINATION SPECTRUM</span>
            <span>MARGIN: {(margin * 100).toFixed(2)} pts (Req: {(marginThreshold * 100).toFixed(1)} pts)</span>
          </div>
          <div className="w-full bg-archive-parchment h-2 rounded-full overflow-hidden border border-archive-hairline">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(margin * 400, 100)}%` }}
              transition={{ type: 'spring', stiffness: 100, damping: 20 }}
              className={`h-full ${margin >= marginThreshold ? 'bg-emerald-600' : 'bg-amber-500'}`}
            />
          </div>
        </div>
      </div>

      {/* 4. Multimodal Diagnostics Grid (GPS + Gatekeeper + Quality) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* GPS Evidence */}
        <div className="bg-archive-alabaster/80 border border-archive-hairline rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-archive-muted mb-2">
              <span className="flex items-center gap-1.5 font-semibold text-archive-charcoal">
                <Compass className="w-3.5 h-3.5 text-archive-terracotta" />
                EXIF GPS SENSOR
              </span>
              <span className="text-[10px] font-bold">
                {gpsEvidence?.has_gps ? (gpsEvidence.gps_conflict ? 'CONFLICT' : 'DETECTED') : 'STRIPPED'}
              </span>
            </div>

            {gpsEvidence?.has_gps ? (
              <div className="space-y-1.5 font-mono text-xs">
                {gpsEvidence.coordinates && (
                  <div className="flex justify-between text-archive-stone">
                    <span>COORDS:</span>
                    <span className="font-medium text-archive-charcoal">
                      {gpsEvidence.coordinates.lat.toFixed(4)}°, {gpsEvidence.coordinates.lng.toFixed(4)}°
                    </span>
                  </div>
                )}
                {gpsEvidence.distance_km !== null && (
                  <div className="flex justify-between text-archive-stone">
                    <span>SITE DISTANCE:</span>
                    <span className="font-bold text-archive-charcoal">{gpsEvidence.distance_km} km</span>
                  </div>
                )}
                <p className="text-[11px] font-sans text-archive-stone pt-1 border-t border-archive-hairline mt-1">
                  {gpsEvidence.note}
                </p>
              </div>
            ) : (
              <p className="text-xs text-archive-stone font-sans leading-relaxed">
                No GPS tags found in image EXIF. Vector search proceeds solely via local visual CLIP embeddings without penalty.
              </p>
            )}
          </div>
        </div>

        {/* Gatekeeper Evidence */}
        <div className="bg-archive-alabaster/80 border border-archive-hairline rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-archive-muted mb-2">
              <span className="flex items-center gap-1.5 font-semibold text-archive-charcoal">
                <Cpu className="w-3.5 h-3.5 text-archive-terracotta" />
                ARCHITECTURAL GATEKEEPER
              </span>
              <span className="font-mono font-bold text-archive-charcoal">{gatekeeperPct}%</span>
            </div>

            <div className="w-full bg-archive-parchment h-2 rounded-full overflow-hidden border border-archive-hairline/80 my-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(gatekeeperPct, 100)}%` }}
                transition={{ type: 'spring', stiffness: 100, damping: 20 }}
                className={`h-full ${
                  gatekeeperPct >= 55
                    ? 'bg-emerald-600'
                    : gatekeeperPct >= 45
                    ? 'bg-amber-600'
                    : 'bg-rose-600'
                }`}
              />
            </div>

            <p className="text-xs text-archive-stone font-sans mt-2">
              {gatekeeperPct >= 55
                ? 'High architectural probability. Clear monument features recognized.'
                : gatekeeperPct >= 45
                ? 'Marginal architectural signature; candidate for human review or Tier 2.'
                : 'Failed architectural gatekeeper. Classified as non-monument.'}
            </p>
          </div>
        </div>

        {/* Image Quality Evidence */}
        <div className="bg-archive-alabaster/80 border border-archive-hairline rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-archive-muted mb-2">
              <span className="flex items-center gap-1.5 font-semibold text-archive-charcoal">
                <Camera className="w-3.5 h-3.5 text-archive-terracotta" />
                SPECIMEN QUALITY
              </span>
              <span className={`text-[10px] font-bold ${quality?.passed_quality_check !== false ? 'text-emerald-700' : 'text-rose-700'}`}>
                {quality?.passed_quality_check !== false ? 'PASSED' : 'DEGRADED'}
              </span>
            </div>

            {quality ? (
              <div className="space-y-1 font-mono text-xs">
                <div className="flex justify-between text-archive-stone">
                  <span>DIMENSIONS:</span>
                  <span className="font-medium text-archive-charcoal">{quality.width}x{quality.height} px</span>
                </div>
                <div className="flex justify-between text-archive-stone">
                  <span>FOCUS (LAPLACIAN):</span>
                  <span className={`font-medium ${quality.is_blurry ? 'text-rose-700 font-bold' : 'text-archive-charcoal'}`}>
                    {quality.blur_score} {quality.is_blurry ? '(BLURRY)' : ''}
                  </span>
                </div>
                <div className="flex justify-between text-archive-stone">
                  <span>EXPOSURE:</span>
                  <span className="font-medium text-archive-charcoal">
                    {quality.is_underexposed ? 'UNDEREXPOSED' : quality.is_overexposed ? 'OVEREXPOSED' : 'BALANCED'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-archive-stone font-sans leading-relaxed">
                Standard image inspection passed.
              </p>
            )}
          </div>
        </div>

      </div>

      {/* 5. Grounded Reason Codes */}
      {reasonCodes.length > 0 && (
        <div className="pt-1">
          <div className="text-[10px] font-mono uppercase text-archive-muted tracking-wider mb-2 font-bold">
            UNCERTAINTY ENGINE REASON CODES:
          </div>
          <div className="flex flex-wrap gap-1.5">
            {reasonCodes.map((code, idx) => (
              <span
                key={idx}
                className="font-mono text-[11px] px-2.5 py-1 rounded bg-white border border-archive-hairline text-archive-charcoal shadow-sm flex items-center gap-1"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-archive-terracotta"></span>
                {code}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 6. Decision Rationale Monograph */}
      <div className="bg-archive-alabaster/60 border border-archive-hairline p-3.5 rounded text-xs font-sans text-archive-stone leading-relaxed">
        <span className="font-mono text-[10px] uppercase font-bold text-archive-charcoal block mb-1">
          CURATORIAL DECISION RATIONALE:
        </span>
        {uncertainty?.explanation || decision_reason}
      </div>

    </div>
  );
}
