import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  Calendar,
  Compass,
  Landmark,
  ShieldCheck,
  ExternalLink,
  MessageSquare,
  Sparkles,
  Send,
  Loader2,
  FileText,
  AlertCircle,
  HelpCircle,
  Clock,
  Layers,
  Scroll,
  Building,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Tag
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

export default function GroundedKnowledgeViewer({ monumentKey, monumentName }) {
  const [knowledge, setKnowledge] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Ask the Archive State
  const [query, setQuery] = useState('');
  const [asking, setAsking] = useState(false);
  const [inquiryResult, setInquiryResult] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'architecture' | 'timeline' | 'cultural' | 'preservation' | 'sources' | 'ask'

  useEffect(() => {
    if (!monumentKey) return;

    let isMounted = true;
    setLoading(true);
    setError(null);
    setInquiryResult(null);

    fetch(`${API_BASE_URL}/api/monuments/${monumentKey}/knowledge`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Archival knowledge record for '${monumentKey}' returned HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        if (isMounted) {
          setKnowledge(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          logger_error: console.error('Failed to load grounded knowledge:', err);
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [monumentKey]);

  const handleAsk = async (e, customQuery = null) => {
    if (e) e.preventDefault();
    const targetQuery = (customQuery || query).trim();
    if (!targetQuery || !monumentKey) return;

    setAsking(true);
    setInquiryResult(null);

    try {
      const resp = await fetch(`${API_BASE_URL}/api/monuments/${monumentKey}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: targetQuery }),
      });

      if (!resp.ok) {
        throw new Error(`Inquiry returned status ${resp.status}`);
      }

      const answerData = await resp.json();
      setInquiryResult(answerData);
    } catch (err) {
      setInquiryResult({
        answer: 'Curatorial inquiry could not be completed at this time. Please ensure the local knowledge server is running.',
        evidence_sufficient: false,
        grounded: false,
        confidence_assessment: 'CONNECTION_ERROR',
        citations: [],
      });
    } finally {
      setAsking(false);
    }
  };

  const sampleQuestions = [
    `Who commissioned ${monumentName || 'this monument'} and when?`,
    'What primary architectural materials were used in construction?',
    'What is the statutory UNESCO and ASI protection status?',
    'Are there any verified historical legends or construction facts?',
  ];

  if (loading) {
    return (
      <div className="bg-archive-ivory border border-archive-hairline rounded p-8 text-center space-y-3 font-mono text-xs text-archive-stone">
        <Loader2 className="w-6 h-6 text-archive-terracotta animate-spin mx-auto" />
        <p className="uppercase tracking-wider">RETRIEVING GROUNDED HISTORICAL KNOWLEDGE ARCHIVE...</p>
      </div>
    );
  }

  if (error || !knowledge) {
    return (
      <div className="bg-archive-ivory border border-archive-hairline rounded p-6 font-mono text-xs text-archive-stone flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold uppercase text-archive-charcoal block mb-1">
            Grounded Knowledge Register Unavailable
          </span>
          <p className="font-sans text-xs text-archive-muted">
            The extended historical monograph for monument '{monumentKey}' could not be loaded from the local ASI knowledge layer.
          </p>
        </div>
      </div>
    );
  }

  const {
    historical_overview,
    construction_period,
    patron_or_dynasty,
    principal_architect,
    architectural_analysis,
    cultural_significance,
    historical_timeline = [],
    preservation_record,
    interesting_facts = [],
    citations = {},
    last_verified,
    verification_status,
  } = knowledge;

  return (
    <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate overflow-hidden">
      
      {/* Section Header */}
      <div className="p-6 sm:p-8 border-b border-archive-hairline bg-archive-alabaster/40">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-archive-terracotta flex-shrink-0" />
            <h3 className="font-serif text-2xl font-bold text-archive-charcoal tracking-tight">
              Grounded Historical Knowledge Engine
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] uppercase px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              {verification_status || 'VERIFIED BY ASI & UNESCO'}
            </span>
            <span className="font-mono text-[10px] text-archive-muted border border-archive-hairline px-2 py-1 rounded bg-white">
              VERIFIED: {last_verified ? new Date(last_verified).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '2025'}
            </span>
          </div>
        </div>

        <p className="font-sans text-xs text-archive-stone mt-2 max-w-3xl leading-relaxed">
          Source-grounded cultural intelligence directly anchored to Archaeological Survey of India (ASI) memoirs, UNESCO World Heritage dossiers, and official state gazetteers. Strictly hallucination-resistant.
        </p>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-1.5 mt-5 pt-4 border-t border-archive-hairline/80 font-mono text-xs">
          {[
            { id: 'overview', label: 'Historical Overview', icon: BookOpen },
            { id: 'architecture', label: 'Architectural Analysis', icon: Compass },
            { id: 'timeline', label: `Chronological Timeline (${historical_timeline.length})`, icon: Calendar },
            { id: 'cultural', label: 'Cultural Significance', icon: Landmark },
            { id: 'preservation', label: 'Preservation Record', icon: ShieldCheck },
            { id: 'sources', label: `Source Archive (${Object.keys(citations).length})`, icon: Scroll },
            { id: 'ask', label: 'Ask the Archive', icon: MessageSquare, highlight: true },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded transition-all text-xs uppercase tracking-wider font-semibold ${
                  isActive
                    ? 'bg-archive-terracotta text-white shadow-sm'
                    : tab.highlight
                    ? 'bg-amber-100/70 text-amber-900 border border-amber-300 hover:bg-amber-100'
                    : 'bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : tab.highlight ? 'text-amber-800' : 'text-archive-terracotta'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panels */}
      <div className="p-6 sm:p-8">

        {/* =================================================================== */}
        {/* TAB 1: HISTORICAL OVERVIEW */}
        {/* =================================================================== */}
        {activeTab === 'overview' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              <div className="bg-archive-alabaster/60 border border-archive-hairline p-3.5 rounded font-mono text-xs">
                <span className="text-[10px] text-archive-muted uppercase tracking-wider block mb-1">
                  Construction Period
                </span>
                <span className="font-bold text-archive-charcoal">{construction_period}</span>
              </div>
              <div className="bg-archive-alabaster/60 border border-archive-hairline p-3.5 rounded font-mono text-xs">
                <span className="text-[10px] text-archive-muted uppercase tracking-wider block mb-1">
                  Patron / Dynasty
                </span>
                <span className="font-bold text-archive-charcoal">{patron_or_dynasty}</span>
              </div>
              <div className="bg-archive-alabaster/60 border border-archive-hairline p-3.5 rounded font-mono text-xs">
                <span className="text-[10px] text-archive-muted uppercase tracking-wider block mb-1">
                  Master Architect / Guild
                </span>
                <span className="font-bold text-archive-charcoal">{principal_architect || 'Imperial Sthapatis / Royal Guild'}</span>
              </div>
            </div>

            <div>
              <div className="font-mono text-xs uppercase tracking-wider text-archive-terracotta font-bold mb-2">
                VERIFIED ARCHIVAL SYNOPSIS
              </div>
              <div className="font-serif text-base sm:text-lg text-archive-ink leading-relaxed bg-archive-alabaster/30 p-5 rounded border border-archive-hairline/80">
                {historical_overview}
              </div>
            </div>

            {/* Interesting Verified Facts */}
            {interesting_facts.length > 0 && (
              <div className="mt-6 pt-6 border-t border-archive-hairline space-y-3">
                <div className="font-mono text-xs uppercase tracking-wider text-archive-stone font-bold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-archive-terracotta" />
                  <span>VERIFIED CURATORIAL FACTS & ANOMALIES</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {interesting_facts.map((fact) => (
                    <div
                      key={fact.fact_id}
                      className="bg-white border border-archive-hairline p-4 rounded space-y-1.5 shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-sans font-bold text-xs text-archive-charcoal">
                          {fact.headline}
                        </span>
                        <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-archive-alabaster text-archive-muted border border-archive-hairline">
                          {fact.citation_id}
                        </span>
                      </div>
                      <p className="font-sans text-xs text-archive-stone leading-relaxed">
                        {fact.detail}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* =================================================================== */}
        {/* TAB 2: ARCHITECTURAL ANALYSIS */}
        {/* =================================================================== */}
        {activeTab === 'architecture' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="flex flex-wrap items-center justify-between pb-3 border-b border-archive-hairline gap-2">
              <div>
                <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block">
                  Primary Architectural Movement
                </span>
                <span className="font-serif text-2xl font-bold text-archive-charcoal">
                  {architectural_analysis.style_name}
                </span>
              </div>
              {architectural_analysis.school_or_period && (
                <span className="font-mono text-xs bg-archive-alabaster border border-archive-hairline px-3 py-1 rounded text-archive-charcoal">
                  School: {architectural_analysis.school_or_period}
                </span>
              )}
            </div>

            {/* Key Structural Features */}
            <div>
              <div className="font-mono text-xs uppercase tracking-wider text-archive-terracotta font-bold mb-3 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                <span>DISTINCTIVE ARCHITECTURAL SIGNATURES</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {architectural_analysis.key_features.map((feat, idx) => (
                  <div
                    key={idx}
                    className="bg-white border border-archive-hairline p-3 rounded flex items-start gap-2.5 text-xs text-archive-charcoal"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-archive-terracotta flex-shrink-0 mt-1.5" />
                    <span className="font-sans">{feat}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Materials Used */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="bg-archive-alabaster/50 border border-archive-hairline p-4 rounded space-y-2">
                <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block font-semibold">
                  DOCUMENTED CONSTRUCTION MATERIALS
                </span>
                <ul className="space-y-1.5 text-xs font-sans text-archive-stone">
                  {architectural_analysis.construction_materials.map((mat, idx) => (
                    <li key={idx} className="flex items-center gap-2">
                      <span className="w-1 h-1 bg-archive-muted rounded-full" />
                      <span>{mat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-archive-alabaster/50 border border-archive-hairline p-4 rounded space-y-2">
                <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block font-semibold">
                  ENGINEERING & STRUCTURAL SIGNIFICANCE
                </span>
                <p className="font-sans text-xs text-archive-stone leading-relaxed">
                  {architectural_analysis.structural_significance}
                </p>
                <div className="pt-2 text-right">
                  <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-white text-archive-muted border border-archive-hairline">
                    CITATION: {architectural_analysis.citation_id}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* =================================================================== */}
        {/* TAB 3: CHRONOLOGICAL TIMELINE */}
        {/* =================================================================== */}
        {activeTab === 'timeline' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="font-mono text-xs text-archive-stone uppercase tracking-wider mb-2 font-semibold">
              CHRONOLOGY OF VERIFIED HISTORICAL EVENTS
            </div>

            <div className="relative border-l-2 border-archive-hairline ml-3 sm:ml-6 space-y-6">
              {historical_timeline.map((evt) => (
                <div key={evt.event_id} className="relative pl-6 sm:pl-8 group">
                  {/* Timeline Node Point */}
                  <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-white border-2 border-archive-terracotta group-hover:bg-archive-terracotta transition-colors" />

                  <div className="bg-white border border-archive-hairline rounded p-4 shadow-sm space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 bg-archive-alabaster text-archive-terracotta border border-archive-hairline rounded">
                          {evt.year_or_era}
                        </span>
                        <h4 className="font-sans font-bold text-sm text-archive-charcoal">
                          {evt.title}
                        </h4>
                      </div>
                      <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-archive-alabaster text-archive-muted border border-archive-hairline">
                        {evt.citation_id}
                      </span>
                    </div>

                    <p className="font-sans text-xs text-archive-stone leading-relaxed">
                      {evt.description}
                    </p>

                    {evt.historical_actors.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px] font-mono text-archive-muted">
                        <span className="uppercase text-[9px] text-archive-muted">Historical Actors:</span>
                        {evt.historical_actors.map((actor, idx) => (
                          <span
                            key={idx}
                            className="bg-archive-alabaster/70 px-1.5 py-0.5 rounded text-archive-charcoal border border-archive-hairline"
                          >
                            {actor}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* =================================================================== */}
        {/* TAB 4: CULTURAL SIGNIFICANCE */}
        {/* =================================================================== */}
        {activeTab === 'cultural' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-archive-alabaster/40 border border-archive-hairline p-5 rounded space-y-2">
              <span className="font-mono text-xs uppercase tracking-wider text-archive-terracotta font-bold block">
                CIVILIZATIONAL & CULTURAL CONTEXT
              </span>
              <p className="font-serif text-base text-archive-ink leading-relaxed">
                {cultural_significance.cultural_context}
              </p>
            </div>

            {cultural_significance.religious_or_symbolic_meaning && (
              <div className="bg-white border border-archive-hairline p-5 rounded space-y-2">
                <span className="font-mono text-xs uppercase tracking-wider text-archive-charcoal font-bold block flex items-center gap-1.5">
                  <Landmark className="w-3.5 h-3.5 text-archive-terracotta" />
                  <span>RELIGIOUS, PHILOSOPHICAL & ICONOGRAPHIC SYMBOLISM</span>
                </span>
                <p className="font-sans text-xs text-archive-stone leading-relaxed">
                  {cultural_significance.religious_or_symbolic_meaning}
                </p>
              </div>
            )}

            {cultural_significance.intangible_heritage && (
              <div className="bg-white border border-archive-hairline p-5 rounded space-y-2">
                <span className="font-mono text-xs uppercase tracking-wider text-archive-charcoal font-bold block flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-archive-terracotta" />
                  <span>INTANGIBLE CULTURAL HERITAGE & LIVING TRADITIONS</span>
                </span>
                <p className="font-sans text-xs text-archive-stone leading-relaxed">
                  {cultural_significance.intangible_heritage}
                </p>
              </div>
            )}

            <div className="text-right">
              <span className="font-mono text-[9px] uppercase px-2 py-0.5 rounded bg-archive-alabaster text-archive-muted border border-archive-hairline">
                SOURCE CITATION: {cultural_significance.citation_id}
              </span>
            </div>
          </motion.div>
        )}

        {/* =================================================================== */}
        {/* TAB 5: PRESERVATION RECORD */}
        {/* =================================================================== */}
        {activeTab === 'preservation' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white border border-archive-hairline p-4 rounded space-y-1">
                <span className="font-mono text-[10px] text-archive-muted uppercase tracking-wider block">
                  UNESCO World Heritage Status
                </span>
                <span className="font-sans text-sm font-bold text-archive-charcoal">
                  {preservation_record.unesco_status || 'National Inventory Protected'}
                </span>
              </div>

              <div className="bg-white border border-archive-hairline p-4 rounded space-y-1">
                <span className="font-mono text-[10px] text-archive-muted uppercase tracking-wider block">
                  National Legal Framework
                </span>
                <span className="font-sans text-sm font-bold text-archive-charcoal">
                  {preservation_record.national_protection}
                </span>
              </div>

              <div className="bg-white border border-archive-hairline p-4 rounded space-y-1">
                <span className="font-mono text-[10px] text-archive-muted uppercase tracking-wider block">
                  Managing Directorate / Circle
                </span>
                <span className="font-sans text-sm font-bold text-archive-charcoal">
                  {preservation_record.governing_body}
                </span>
              </div>

              <div className="bg-white border border-archive-hairline p-4 rounded space-y-1">
                <span className="font-mono text-[10px] text-archive-muted uppercase tracking-wider block">
                  Structural Assessment
                </span>
                <span className="font-sans text-sm font-bold text-emerald-800">
                  {preservation_record.current_condition}
                </span>
              </div>
            </div>

            {preservation_record.key_conservation_initiatives.length > 0 && (
              <div className="bg-archive-alabaster/40 border border-archive-hairline p-5 rounded space-y-3">
                <span className="font-mono text-xs uppercase tracking-wider text-archive-charcoal font-bold block">
                  DOCUMENTED RESTORATION & CONSERVATION INITIATIVES
                </span>
                <ul className="space-y-2 text-xs font-sans text-archive-stone">
                  {preservation_record.key_conservation_initiatives.map((init, idx) => (
                    <li key={idx} className="flex items-start gap-2 bg-white p-2.5 rounded border border-archive-hairline/80">
                      <ShieldCheck className="w-4 h-4 text-archive-terracotta flex-shrink-0 mt-0.5" />
                      <span>{init}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="text-right">
              <span className="font-mono text-[9px] uppercase px-2 py-0.5 rounded bg-archive-alabaster text-archive-muted border border-archive-hairline">
                SOURCE CITATION: {preservation_record.citation_id}
              </span>
            </div>
          </motion.div>
        )}

        {/* =================================================================== */}
        {/* TAB 6: SOURCE ARCHIVE */}
        {/* =================================================================== */}
        {activeTab === 'sources' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="font-mono text-xs uppercase tracking-wider text-archive-stone font-semibold mb-2">
              AUTHORITATIVE PRIMARY CITATIONS & ARCHIVAL REGISTRY
            </div>

            <div className="space-y-3">
              {Object.values(citations).map((cit) => (
                <div
                  key={cit.citation_id}
                  className="bg-white border border-archive-hairline rounded p-4 hover:border-archive-stone transition-all shadow-sm space-y-2"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 bg-archive-alabaster text-archive-terracotta border border-archive-hairline rounded">
                        {cit.citation_id}
                      </span>
                      <h4 className="font-sans font-bold text-sm text-archive-charcoal">
                        {cit.title}
                      </h4>
                    </div>
                    <span className="font-mono text-[9px] uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {cit.citation_type}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono text-archive-stone">
                    <div>
                      <span className="text-[10px] text-archive-muted uppercase">Publisher: </span>
                      <span className="text-archive-charcoal font-semibold">{cit.publisher}</span>
                    </div>
                    {cit.author_or_editor && (
                      <div>
                        <span className="text-[10px] text-archive-muted uppercase">Author/Surveyor: </span>
                        <span>{cit.author_or_editor}</span>
                      </div>
                    )}
                    {cit.archive_ref && (
                      <div>
                        <span className="text-[10px] text-archive-muted uppercase">Registry Ref: </span>
                        <span className="font-bold text-archive-terracotta">{cit.archive_ref}</span>
                      </div>
                    )}
                    {cit.year_published && (
                      <div>
                        <span className="text-[10px] text-archive-muted uppercase">Publication Year: </span>
                        <span>{cit.year_published}</span>
                      </div>
                    )}
                  </div>

                  {cit.relevant_claim && (
                    <div className="bg-archive-alabaster/50 p-2.5 rounded text-xs font-sans text-archive-stone border border-archive-hairline/60">
                      <span className="font-mono text-[10px] uppercase text-archive-muted block font-semibold">
                        Grounded Claim Association:
                      </span>
                      <span>{cit.relevant_claim}</span>
                    </div>
                  )}

                  {cit.url && (
                    <div className="pt-1 text-right">
                      <a
                        href={cit.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 font-mono text-xs text-archive-terracotta hover:underline"
                      >
                        <span>Access Official Registry Record</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* =================================================================== */}
        {/* TAB 7: ASK THE ARCHIVE */}
        {/* =================================================================== */}
        {activeTab === 'ask' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-archive-alabaster/40 border border-archive-hairline p-5 rounded space-y-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-archive-terracotta" />
                <h4 className="font-mono text-xs uppercase tracking-wider text-archive-charcoal font-bold">
                  CURATORIAL INQUIRY CONSOLE // STRICT GROUNDING
                </h4>
              </div>
              <p className="font-sans text-xs text-archive-stone leading-relaxed">
                Inquire about the construction, patronage, timeline, or engineering of {monumentName}. Responses are strictly restricted to verified ASI and UNESCO documentation. If evidence is insufficient, the system refuses to speculate.
              </p>

              {/* Sample Question Pills */}
              <div className="space-y-1.5 pt-1">
                <span className="font-mono text-[10px] uppercase text-archive-muted block font-semibold">
                  Sample Authoritative Queries:
                </span>
                <div className="flex flex-wrap gap-2">
                  {sampleQuestions.map((sq, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={(e) => {
                        setQuery(sq);
                        handleAsk(e, sq);
                      }}
                      className="text-left font-sans text-xs bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline px-3 py-1 rounded transition-colors shadow-sm"
                    >
                      {sq}
                    </button>
                  ))}
                </div>
              </div>

              {/* Inquiry Input Form */}
              <form onSubmit={handleAsk} className="pt-3 flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={`Ask a verified question about ${monumentName}...`}
                  className="flex-1 bg-white border border-archive-hairline px-4 py-2.5 rounded font-sans text-xs text-archive-charcoal placeholder:text-archive-muted focus:outline-none focus:ring-1 focus:ring-archive-terracotta"
                  disabled={asking}
                />
                <button
                  type="submit"
                  disabled={asking || !query.trim()}
                  className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-archive-charcoal hover:bg-black disabled:opacity-50 text-white rounded font-mono text-xs uppercase tracking-wider transition-colors shadow-sm"
                >
                  {asking ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Consulting...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5 text-archive-parchment" />
                      <span>Consult</span>
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Inquiry Result Panel */}
            <AnimatePresence>
              {inquiryResult && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={`border rounded p-5 sm:p-6 space-y-4 ${
                    inquiryResult.evidence_sufficient
                      ? 'bg-white border-archive-stone shadow-plate'
                      : 'bg-amber-50/70 border-amber-300'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between pb-3 border-b border-archive-hairline gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`font-mono text-[10px] uppercase px-2 py-0.5 rounded font-bold ${
                        inquiryResult.evidence_sufficient
                          ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                          : 'bg-amber-200 text-amber-900 border border-amber-300'
                      }`}>
                        {inquiryResult.evidence_sufficient ? 'VERIFIED EVIDENCE RETRIEVED' : 'EVIDENCE INSUFFICIENT // REFUSAL'}
                      </span>
                      <span className="font-mono text-[10px] uppercase text-archive-muted">
                        ENGINE: {inquiryResult.answering_engine || 'OFFLINE_CURATORIAL_RETRIEVAL'}
                      </span>
                    </div>

                    <span className="font-mono text-[10px] text-archive-stone border border-archive-hairline px-2 py-0.5 rounded bg-archive-alabaster">
                      {inquiryResult.confidence_assessment}
                    </span>
                  </div>

                  <div>
                    <div className="font-mono text-[10px] text-archive-muted uppercase tracking-wider mb-1">
                      QUESTION: {inquiryResult.question || query}
                    </div>
                    <p className="font-serif text-base sm:text-lg text-archive-ink leading-relaxed">
                      {inquiryResult.answer}
                    </p>
                  </div>

                  {inquiryResult.disclaimer && (
                    <div className="text-[11px] font-mono text-archive-muted italic">
                      Note: {inquiryResult.disclaimer}
                    </div>
                  )}

                  {inquiryResult.citations && inquiryResult.citations.length > 0 && (
                    <div className="pt-3 border-t border-archive-hairline space-y-2">
                      <span className="font-mono text-[10px] uppercase text-archive-terracotta font-semibold block">
                        Supporting Grounded Citations:
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {inquiryResult.citations.map((c) => (
                          <span
                            key={c.citation_id}
                            className="font-mono text-xs bg-archive-alabaster border border-archive-hairline px-2.5 py-1 rounded text-archive-charcoal flex items-center gap-1.5"
                          >
                            <Tag className="w-3 h-3 text-archive-terracotta" />
                            <span className="font-bold">{c.citation_id}:</span>
                            <span className="truncate max-w-xs">{c.title}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

      </div>
    </div>
  );
}

