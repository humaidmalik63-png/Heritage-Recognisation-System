import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  MapPin,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  BookOpen,
  ShieldCheck,
  RotateCcw,
  Sparkles,
} from 'lucide-react';

export default function MobileResults({ result, onNewScan }) {
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [showCitations, setShowCitations] = useState(true);

  if (!result) return null;

  const isVerified = result.verification_status === 'VERIFIED_MATCH' && !result.is_uncertain;
  const isTier2 = (result.verification_tier || '').includes('TIER 2');
  const isUncertain = result.is_uncertain || result.verification_status === 'UNKNOWN_HERITAGE_SPECIMEN';

  const confidenceScore = result.confidence_score
    ? typeof result.confidence_score === 'number'
      ? result.confidence_score.toFixed(1)
      : result.confidence_score
    : '85.0';

  const coords = result.coordinates;
  const citations = result.grounded_citations || {};
  const candidates = result.pipeline_telemetry?.top_3_candidates || [];

  return (
    <div className="space-y-4 pb-8">
      {/* Verification Status Ribbon */}
      <div
        className={`p-3 rounded-xl border flex items-center justify-between gap-2 shadow-2xs ${
          isVerified
            ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
            : isUncertain
            ? 'bg-amber-50 border-amber-200 text-amber-950'
            : 'bg-[#FFFEFA] border-[#E3DFD5] text-[#171816]'
        }`}
      >
        <div className="flex items-center gap-2">
          {isVerified ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          )}
          <div>
            <span className="font-mono text-[9px] uppercase tracking-wider block font-bold">
              {isTier2 ? 'TIER 2 // VLM ADJUDICATED' : '512-D VECTOR MATCH'}
            </span>
            <p className="font-semibold text-xs leading-tight">
              {isVerified
                ? 'Catalogued Monument Match'
                : 'Ambiguous Specimen — Review Needed'}
            </p>
          </div>
        </div>

        <div className="text-right flex-shrink-0">
          <span className="font-mono text-sm font-extrabold text-[#A9472D]">
            {confidenceScore}%
          </span>
          <span className="block text-[8px] font-mono text-[#6E7069] uppercase">
            Confidence
          </span>
        </div>
      </div>

      {/* Main Archival Dossier Card */}
      <div className="p-4 rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] shadow-xs space-y-4">
        {/* Archival Stamp & Catalog ID */}
        <div className="flex items-center justify-between border-b border-[#E3DFD5]/60 pb-2">
          <span className="px-2 py-0.5 rounded bg-[#ECE8DD] text-[9px] font-mono font-bold text-[#171816] uppercase">
            {result.catalog_id || 'ASI-ARCH-REG'}
          </span>
          <span className="text-[10px] font-mono text-[#6E7069]">
            {result.monument_key || 'verified_match'}
          </span>
        </div>

        {/* Monument Title & Location */}
        <div>
          <h2 className="font-serif text-2xl font-bold text-[#171816] leading-tight">
            {result.monument_name || 'Architectural Specimen'}
          </h2>
          <div className="flex items-center gap-1.5 text-xs text-[#6E7069] font-sans mt-1">
            <MapPin className="w-3.5 h-3.5 text-[#A9472D] flex-shrink-0" />
            <span>{result.location || 'Location Recorded'}</span>
          </div>
        </div>

        {/* Style & Era Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2.5 rounded-xl bg-[#F5F3ED] border border-[#E3DFD5]">
            <span className="text-[9px] font-mono text-[#6E7069] uppercase block font-semibold">
              ARCHITECTURAL STYLE
            </span>
            <p className="font-medium text-[#171816] mt-0.5 text-xs line-clamp-2">
              {result.architectural_style || 'Historic Heritage Architecture'}
            </p>
          </div>

          <div className="p-2.5 rounded-xl bg-[#F5F3ED] border border-[#E3DFD5]">
            <span className="text-[9px] font-mono text-[#6E7069] uppercase block font-semibold">
              HISTORICAL ERA
            </span>
            <p className="font-medium text-[#171816] mt-0.5 text-xs line-clamp-2">
              {result.built_by_or_era || 'Historical Antiquity'}
            </p>
          </div>
        </div>

        {/* Curatorial Monograph */}
        {result.historical_summary && (
          <div className="space-y-1 pt-1">
            <span className="text-[10px] font-mono text-[#6E7069] uppercase font-bold tracking-wider">
              CURATORIAL MONOGRAPH
            </span>
            <p className="text-xs text-[#171816] font-serif leading-relaxed">
              {result.historical_summary}
            </p>
          </div>
        )}

        {/* Detected Structural Features */}
        {Array.isArray(result.structural_features_detected) && result.structural_features_detected.length > 0 && (
          <div className="space-y-1.5 pt-1">
            <span className="text-[10px] font-mono text-[#6E7069] uppercase font-bold tracking-wider">
              DETECTED ARCHITECTURAL FEATURES
            </span>
            <div className="flex flex-wrap gap-1.5">
              {result.structural_features_detected.map((feat, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.8 rounded-lg bg-[#ECE8DD] text-[#171816] text-[10px] font-medium"
                >
                  {feat}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Geodetic Coordinates */}
        {coords && (
          <div className="p-3 rounded-xl bg-[#F5F3ED] border border-[#E3DFD5] flex items-center justify-between text-xs">
            <div>
              <span className="text-[9px] font-mono text-[#6E7069] uppercase block">
                GEODETIC POSITION
              </span>
              <span className="font-mono text-xs font-bold text-[#171816]">
                {coords.lat ? `${coords.lat.toFixed(4)}° N, ${coords.lng.toFixed(4)}° E` : 'Geolocated'}
              </span>
            </div>
            {coords.lat && coords.lng && (
              <a
                href={`https://www.openstreetmap.org/?mlat=${coords.lat}&mlon=${coords.lng}&zoom=16`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#FFFEFA] border border-[#E3DFD5] text-[#171816] font-mono text-[10px] font-semibold"
              >
                <span>OSM</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        )}
      </div>

      {/* Grounded Epigraphical Citations (Collapsible) */}
      {citations && Object.keys(citations).length > 0 && (
        <div className="rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] overflow-hidden">
          <button
            onClick={() => setShowCitations(!showCitations)}
            className="w-full p-3.5 flex items-center justify-between text-left text-xs font-semibold text-[#171816] hover:bg-[#F5F3ED]/50"
          >
            <div className="flex items-center gap-1.5 font-mono uppercase text-[#A9472D] text-[11px] font-bold">
              <BookOpen className="w-3.5 h-3.5" />
              <span>Grounded Citations & Sources</span>
            </div>
            {showCitations ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showCitations && (
            <div className="px-3.5 pb-3.5 pt-1 space-y-2 text-xs border-t border-[#E3DFD5]/60">
              {citations.primary_source && (
                <div className="p-2 rounded-lg bg-[#F5F3ED] text-[11px]">
                  <span className="font-mono text-[9px] uppercase text-[#6E7069] block font-bold">
                    PRIMARY ARCHIVAL SOURCE
                  </span>
                  <p className="font-serif text-[#171816] mt-0.5">{citations.primary_source}</p>
                </div>
              )}
              {citations.gazetteer_reference && (
                <div className="p-2 rounded-lg bg-[#F5F3ED] text-[11px]">
                  <span className="font-mono text-[9px] uppercase text-[#6E7069] block font-bold">
                    DISTRICT GAZETTEER
                  </span>
                  <p className="font-serif text-[#171816] mt-0.5">{citations.gazetteer_reference}</p>
                </div>
              )}
              {citations.unesco_whc_ref && (
                <div className="p-2 rounded-lg bg-[#F5F3ED] text-[11px]">
                  <span className="font-mono text-[9px] uppercase text-[#6E7069] block font-bold">
                    UNESCO WORLD HERITAGE REFERENCE
                  </span>
                  <p className="font-serif text-[#171816] mt-0.5">{citations.unesco_whc_ref}</p>
                </div>
              )}
              {citations.epigraphical_records && (
                <div className="p-2 rounded-lg bg-[#F5F3ED] text-[11px]">
                  <span className="font-mono text-[9px] uppercase text-[#6E7069] block font-bold">
                    EPIGRAPHICAL RECORDS
                  </span>
                  <p className="font-serif text-[#171816] mt-0.5">{citations.epigraphical_records}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Uncertainty & Candidate Telemetry (Collapsible) */}
      <div className="rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] overflow-hidden">
        <button
          onClick={() => setShowTelemetry(!showTelemetry)}
          className="w-full p-3.5 flex items-center justify-between text-left text-xs font-semibold text-[#171816] hover:bg-[#F5F3ED]/50"
        >
          <div className="flex items-center gap-1.5 font-mono uppercase text-[#6E7069] text-[11px] font-bold">
            <Sparkles className="w-3.5 h-3.5 text-[#B99A5B]" />
            <span>Candidate Vector Telemetry</span>
          </div>
          {showTelemetry ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showTelemetry && (
          <div className="px-3.5 pb-3.5 pt-1 space-y-2.5 text-xs border-t border-[#E3DFD5]/60">
            {candidates.length > 0 ? (
              <div className="space-y-1.5">
                <span className="text-[9px] font-mono text-[#6E7069] uppercase font-bold">
                  TOP 3 FAISS NEAREST CANDIDATES
                </span>
                {candidates.map((cand, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-[#F5F3ED] flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-medium text-[#171816]">{cand.monument_name}</span>
                      <span className="text-[10px] text-[#6E7069] block font-mono">
                        {cand.monument_key}
                      </span>
                    </div>
                    <span className="font-mono text-xs font-bold text-[#A9472D]">
                      {(cand.cosine_similarity * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[#6E7069] text-xs">Vector candidates resolved directly via Tier 2 adjudication.</p>
            )}

            {result.pipeline_telemetry?.decision_reason && (
              <div className="p-2 rounded-lg bg-[#ECE8DD] text-[10px] font-mono text-[#171816]">
                <span className="font-bold uppercase block text-[#6E7069]">DECISION RATIONALE</span>
                <p className="mt-0.5">{result.pipeline_telemetry.decision_reason}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action CTA: New Scan */}
      <div className="pt-2">
        <button
          onClick={onNewScan}
          className="w-full py-3.5 px-4 rounded-xl bg-[#171816] hover:bg-[#A9472D] text-[#FFFEFA] font-mono text-xs uppercase font-bold tracking-wider flex items-center justify-center gap-2 shadow-xs transition-colors cursor-pointer active:scale-98"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Deposit Another Specimen</span>
        </button>
      </div>
    </div>
  );
}

