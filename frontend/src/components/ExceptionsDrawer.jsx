import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Send,
  Filter,
  Check,
  Building,
  HelpCircle,
  History,
  Layers,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { fetchExceptions, resolveException } from '../api';

export default function ExceptionsDrawer({ isOpen, onClose, onCountChange }) {
  const [exceptions, setExceptions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState('ALL'); // ALL, PENDING_REVIEW, APPROVED, REJECTED, CATALOGED
  const [selectedResolutions, setSelectedResolutions] = useState({}); // { [id]: { status: 'APPROVED', notes: '' } }
  const [expandedHistories, setExpandedHistories] = useState({});
  const [submittingId, setSubmittingId] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await fetchExceptions();
      const list = Array.isArray(data?.exceptions) ? data.exceptions : Array.isArray(data) ? data : [];
      setExceptions(list);
      const pendingCount = list.filter((e) => e.status === 'PENDING_REVIEW').length;
      if (onCountChange) onCountChange(pendingCount);
    } catch (err) {
      console.warn('Could not load exceptions:', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleResolutionChange = (id, field, value) => {
    setSelectedResolutions((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] || { status: 'APPROVED', notes: '' }),
        [field]: value,
      },
    }));
  };

  const toggleHistory = (id) => {
    setExpandedHistories((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleResolveSubmit = async (item) => {
    const config = selectedResolutions[item.id] || { status: 'APPROVED', notes: '' };
    if (!config.notes?.trim()) {
      alert('Please provide curator notes before submitting a resolution.');
      return;
    }

    setSubmittingId(item.id);
    try {
      await resolveException(item.id, config.status, config.notes.trim());
      setStatusMessage(`Exception #${item.id} resolved as ${config.status}.`);
      setTimeout(() => setStatusMessage(null), 3000);
      await loadData();
    } catch (err) {
      alert(`Resolution failed: ${err.message}`);
    } finally {
      setSubmittingId(null);
    }
  };

  const filteredItems = exceptions.filter((item) => {
    if (filter === 'ALL') return true;
    return item.status === filter;
  });

  const pendingCount = exceptions.filter((e) => e.status === 'PENDING_REVIEW').length;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop Fade */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-archive-charcoal/40 backdrop-blur-sm"
        />

        {/* Slide-in Drawer */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', stiffness: 220, damping: 25 }}
          className="relative w-full max-w-2xl bg-archive-ivory h-full shadow-2xl flex flex-col border-l border-archive-hairline overflow-hidden z-10"
        >
          {/* Header */}
          <div className="px-6 py-5 bg-archive-parchment/70 border-b border-archive-hairline flex items-center justify-between">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-stamp text-archive-terracotta font-bold flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-archive-terracotta" />
                <span>HUMAN-IN-THE-LOOP CURATORIAL OVERSIGHT // SIH PROJECT NO. 30</span>
              </div>
              <h2 className="font-serif text-2xl font-bold text-archive-charcoal mt-0.5">
                Curator Review Exception Log
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={loadData}
                disabled={isLoading}
                className="p-2 text-archive-stone hover:text-archive-charcoal hover:bg-white rounded border border-transparent hover:border-archive-hairline transition-all"
                title="Refresh Exception Log"
              >
                <RotateCcw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={onClose}
                className="p-2 text-archive-stone hover:text-archive-charcoal hover:bg-white rounded border border-transparent hover:border-archive-hairline transition-all"
                aria-label="Close exception drawer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Filter Bar & Notification */}
          <div className="px-6 py-3 bg-white border-b border-archive-hairline flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-1.5 font-mono">
              <span className="text-archive-muted text-[10px] uppercase mr-1">Filter:</span>
              {['ALL', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'CATALOGED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilter(st)}
                  className={`px-2 py-1 rounded text-[11px] uppercase transition-colors ${
                    filter === st
                      ? 'bg-archive-charcoal text-white font-medium'
                      : 'bg-archive-alabaster text-archive-stone hover:bg-archive-parchment'
                  }`}
                >
                  {st.replace('_', ' ')}
                  {st === 'PENDING_REVIEW' && pendingCount > 0 && (
                    <span className="ml-1 px-1 bg-amber-500 text-white rounded-full text-[9px] font-bold">
                      {pendingCount}
                    </span>
                  )}
                </button>
              ))}
            </div>

            <span className="font-mono text-[11px] text-archive-muted">
              {filteredItems.length} {filteredItems.length === 1 ? 'Record' : 'Records'}
            </span>
          </div>

          {statusMessage && (
            <div className="bg-emerald-50 border-b border-emerald-200 px-6 py-2 text-xs font-mono text-emerald-800 flex items-center gap-2">
              <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

          {/* Exception Items List */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <p className="text-xs text-archive-stone font-sans leading-relaxed bg-archive-alabaster p-3.5 rounded border border-archive-hairline">
              Curator Review satisfies the human-oversight protocol of SIH Project No. 30. Scans flagged for close candidate competition, unindexed architectural motifs, degraded image focus, or geodetic location conflicts are held here for manual verification.
            </p>

            {filteredItems.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-archive-hairline rounded bg-white p-6 space-y-2">
                <ShieldAlert className="w-8 h-8 text-archive-muted mx-auto" />
                <h4 className="font-serif text-lg font-bold text-archive-charcoal">
                  No Exceptions in Queue
                </h4>
                <p className="text-xs text-archive-stone max-w-sm mx-auto font-sans">
                  {filter === 'ALL'
                    ? 'All processed specimens met decisive retrieval thresholds or clean non-heritage rejection gates.'
                    : `No exception records found under status "${filter}".`}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredItems.map((item) => {
                  const currentRes = selectedResolutions[item.id] || {
                    status: 'APPROVED',
                    notes: item.curator_notes || '',
                  };
                  const isPending = item.status === 'PENDING_REVIEW';
                  const isHistoryOpen = Boolean(expandedHistories[item.id]);

                  return (
                    <div
                      key={item.id}
                      className="bg-white border border-archive-hairline rounded shadow-sm p-4 space-y-3 transition-all hover:border-archive-borderDark"
                    >
                      {/* Top Header Row */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-archive-hairline">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-archive-charcoal bg-archive-parchment px-2 py-0.5 rounded border border-archive-hairline">
                            #{item.id}
                          </span>
                          <span className="text-[10px] font-mono text-archive-muted flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'N/A'}
                          </span>
                        </div>

                        <span
                          className={`font-mono text-[10px] uppercase px-2 py-0.5 rounded font-bold ${
                            item.status === 'PENDING_REVIEW'
                              ? 'bg-amber-100 text-amber-900 border border-amber-300'
                              : item.status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                              : item.status === 'CATALOGED'
                              ? 'bg-blue-100 text-blue-900 border border-blue-300'
                              : 'bg-rose-100 text-rose-900 border border-rose-300'
                          }`}
                        >
                          {item.status.replace('_', ' ')}
                        </span>
                      </div>

                      {/* Content Details */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                        <div className="bg-archive-alabaster/60 p-2.5 rounded border border-archive-hairline">
                          <span className="text-[10px] text-archive-muted uppercase block">Nearest Candidate</span>
                          <span className="font-serif font-bold text-sm text-archive-charcoal mt-0.5 block truncate">
                            {item.monument_name_candidate || 'Unassigned Landmark'}
                          </span>
                          <div className="text-[10px] text-archive-stone flex justify-between mt-1">
                            <span>Cosine Similarity:</span>
                            <span className="font-bold">{(item.top_similarity_score * 100).toFixed(1)}%</span>
                          </div>
                          {item.similarity_margin !== null && item.similarity_margin !== undefined && (
                            <div className="text-[10px] text-archive-stone flex justify-between">
                              <span>Candidate Margin:</span>
                              <span className="font-bold text-archive-terracotta">+{item.similarity_margin.toFixed(4)}</span>
                            </div>
                          )}
                        </div>

                        <div className="bg-archive-alabaster/60 p-2.5 rounded border border-archive-hairline">
                          <span className="text-[10px] text-archive-muted uppercase block">Gatekeeper Probability</span>
                          <span className="font-bold text-sm text-archive-terracotta mt-0.5 block">
                            {(item.gatekeeper_score * 100).toFixed(1)}% Heritage Probability
                          </span>
                          <span className="text-[10px] text-archive-stone truncate block mt-1">
                            File: {item.specimen_filename}
                          </span>
                        </div>
                      </div>

                      {/* Reason Codes */}
                      {item.reason_codes && item.reason_codes.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {item.reason_codes.map((rc, idx) => (
                            <span
                              key={idx}
                              className="font-mono text-[9px] uppercase px-1.5 py-0.5 bg-archive-parchment text-archive-stone rounded border border-archive-hairline"
                            >
                              {rc}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Ambiguity Reason */}
                      <div className="text-xs font-sans text-archive-stone bg-amber-50/50 p-2.5 rounded border border-amber-200/60 leading-relaxed">
                        <span className="font-mono text-[10px] text-amber-800 font-bold uppercase block mb-0.5">
                          Trigger Rationale:
                        </span>
                        {item.reason}
                      </div>

                      {/* Previous Curator Notes if resolved */}
                      {item.curator_notes && !isPending && (
                        <div className="text-xs font-sans text-archive-charcoal bg-emerald-50/50 p-2.5 rounded border border-emerald-200/60 leading-relaxed">
                          <span className="font-mono text-[10px] text-emerald-800 font-bold uppercase block mb-0.5">
                            Curatorial Resolution Notes:
                          </span>
                          "{item.curator_notes}"
                        </div>
                      )}

                      {/* Audit History Toggle */}
                      {item.history && item.history.length > 0 && (
                        <div className="pt-1">
                          <button
                            type="button"
                            onClick={() => toggleHistory(item.id)}
                            className="text-[10px] font-mono text-archive-muted hover:text-archive-charcoal flex items-center gap-1"
                          >
                            <History className="w-3 h-3 text-archive-terracotta" />
                            <span>Audit Trail ({item.history.length} {item.history.length === 1 ? 'event' : 'events'})</span>
                            {isHistoryOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>

                          {isHistoryOpen && (
                            <div className="mt-2 pl-3 border-l-2 border-archive-terracotta/40 space-y-1 text-[11px] font-mono text-archive-stone">
                              {item.history.map((h, i) => (
                                <div key={i} className="flex justify-between py-0.5">
                                  <span>{h.action} [{h.new_status || h.status}]</span>
                                  <span className="text-[9px] text-archive-muted">
                                    {h.timestamp ? new Date(h.timestamp).toLocaleTimeString() : ''}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Resolution Action Area */}
                      {isPending && (
                        <div className="pt-2 border-t border-archive-hairline space-y-2.5">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-archive-charcoal">Curator Determination:</span>
                            <div className="flex gap-1.5">
                              {['APPROVED', 'REJECTED', 'CATALOGED'].map((st) => (
                                <button
                                  key={st}
                                  type="button"
                                  onClick={() => handleResolutionChange(item.id, 'status', st)}
                                  className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold transition-colors ${
                                    currentRes.status === st
                                      ? st === 'APPROVED'
                                        ? 'bg-emerald-700 text-white'
                                        : st === 'REJECTED'
                                        ? 'bg-rose-700 text-white'
                                        : 'bg-blue-700 text-white'
                                      : 'bg-archive-parchment text-archive-stone hover:bg-archive-alabaster'
                                  }`}
                                >
                                  {st}
                                </button>
                              ))}
                            </div>
                          </div>

                          <textarea
                            value={currentRes.notes}
                            onChange={(e) => handleResolutionChange(item.id, 'notes', e.target.value)}
                            placeholder="Enter curatorial notes, archaeological verification source, or action taken..."
                            rows={2}
                            className="w-full text-xs font-sans p-2 rounded border border-archive-hairline bg-archive-alabaster/40 focus:outline-none focus:border-archive-terracotta"
                          />

                          <div className="flex justify-end">
                            <button
                              onClick={() => handleResolveSubmit(item)}
                              disabled={submittingId === item.id}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow transition-colors disabled:opacity-50"
                            >
                              <Send className="w-3 h-3 text-archive-parchment" />
                              <span>{submittingId === item.id ? 'Submitting...' : 'Record Decision'}</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 bg-archive-parchment/60 border-t border-archive-hairline flex items-center justify-between text-xs font-mono text-archive-muted">
            <span>SIH25052 COMPLIANT AUDIT TRAIL</span>
            <button
              onClick={onClose}
              className="px-4 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
