import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import {
  History as HistoryIcon,
  Search,
  Trash2,
  ScanLine,
  MapPin,
  Calendar,
  ExternalLink,
  ShieldCheck,
  Landmark,
  X,
  Compass
} from 'lucide-react';
import MonographResult from '../components/MonographResult';

export default function History() {
  const { user, history, clearHistory } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedScan, setSelectedScan] = useState(null);

  const filteredHistory = history.filter((item) => {
    const q = searchTerm.toLowerCase();
    return (
      item.monument_name?.toLowerCase().includes(q) ||
      item.catalog_id?.toLowerCase().includes(q) ||
      item.location?.toLowerCase().includes(q) ||
      item.architectural_style?.toLowerCase().includes(q)
    );
  });

  const formatDate = (isoStr) => {
    if (!isoStr) return 'RECENT';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short',
      }).toUpperCase();
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Top Banner / Ledger Header */}
      <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between pb-4 border-b border-archive-hairline gap-4">
          <div>
            <div className="font-mono text-[10px] uppercase text-archive-terracotta tracking-stamp font-bold flex items-center gap-2 mb-1">
              <span className="w-2 h-2 bg-archive-terracotta"></span>
              CURATORIAL LOG // PERSONAL VERIFICATION REGISTER
            </div>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-archive-charcoal leading-none">
              Archival Survey Log
            </h2>
            <p className="mt-2 text-xs font-sans text-archive-stone">
              Archived survey specimens verified by officer <span className="font-semibold text-archive-charcoal">{user?.name}</span> ({user?.badgeNumber || 'ASI-CURATOR'}).
            </p>
          </div>

          <div className="flex items-center gap-3">
            {history.length > 0 && (
              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  if (window.confirm('Are you sure you want to clear your local archival scan log?')) {
                    clearHistory();
                  }
                }}
                className="px-3 py-1.5 bg-white hover:bg-rose-50 text-archive-stone hover:text-rose-700 border border-archive-hairline hover:border-rose-200 rounded font-mono text-xs uppercase tracking-wider transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear Register</span>
              </motion.button>
            )}

            <Link to="/">
              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                className="px-3.5 py-1.5 bg-archive-charcoal hover:bg-black text-white rounded font-mono text-xs uppercase tracking-wider transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <ScanLine className="w-3.5 h-3.5 text-archive-parchment" />
                <span>New Specimen Scan</span>
              </motion.button>
            </Link>
          </div>
        </div>

        {/* Search & Statistics Bar */}
        <div className="mt-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:max-w-md">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by monument name, catalog ID, or state..."
              className="w-full pl-9 pr-3 py-2 bg-white border border-archive-hairline rounded text-xs font-sans text-archive-charcoal placeholder-archive-muted/60 focus:outline-none focus:border-archive-terracotta focus:ring-1 focus:ring-archive-terracotta transition-colors shadow-inner"
            />
            <Search className="w-4 h-4 text-archive-muted absolute left-3 top-2.5 pointer-events-none" />
          </div>

          <div className="flex items-center gap-3 font-mono text-xs text-archive-stone self-start sm:self-auto">
            <span>REGISTER ENTRIES: <strong className="text-archive-charcoal">{filteredHistory.length}</strong></span>
            <span>•</span>
            <span>STORAGE: <strong className="text-emerald-700">ENCRYPTED LOCAL</strong></span>
          </div>
        </div>
      </div>

      {/* History Grid / List */}
      {filteredHistory.length === 0 ? (
        <div className="bg-archive-ivory border border-archive-hairline rounded p-12 text-center shadow-plate space-y-4">
          <div className="w-16 h-16 rounded-full bg-archive-alabaster border border-archive-hairline flex items-center justify-center mx-auto text-archive-muted">
            <HistoryIcon className="w-8 h-8" />
          </div>
          <h3 className="font-serif text-2xl font-bold text-archive-charcoal">
            {searchTerm ? 'No matching archival records found' : 'No Survey Records in Archival Log'}
          </h3>
          <p className="text-xs text-archive-stone max-w-md mx-auto font-sans leading-relaxed">
            {searchTerm
              ? `No cataloged records match "${searchTerm}". Try searching by state or key name.`
              : 'Deposited and verified photographs will be indexed here with their official ASI catalog stamps, vector confidence scores, and geodetic coordinates.'}
          </p>
          <div className="pt-2">
            <Link to="/">
              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                className="px-4 py-2 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow transition-colors inline-flex items-center gap-2"
              >
                <ScanLine className="w-3.5 h-3.5 text-archive-parchment" />
                <span>Deposit First Specimen</span>
              </motion.button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredHistory.map((item) => (
            <motion.div
              key={item.id}
              whileHover={{ y: -3 }}
              transition={{ type: 'spring', stiffness: 220, damping: 20 }}
              onClick={() => setSelectedScan(item)}
              className="bg-archive-ivory border border-archive-hairline rounded shadow-plate overflow-hidden cursor-pointer group hover:border-archive-terracotta/70 transition-all flex flex-col justify-between"
            >
              <div>
                {/* Thumbnail Plate */}
                <div className="relative h-48 w-full bg-black/5 overflow-hidden border-b border-archive-hairline">
                  <img
                    src={item.thumbnail}
                    alt={item.monument_name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 filter contrast-105"
                    onError={(e) => {
                      e.target.src = `http://localhost:8000/dataset/${item.monument_key}/img_1.jpg`;
                    }}
                  />
                  <div className="absolute top-2.5 left-2.5">
                    <span className="archival-stamp bg-white/95 text-[10px] py-0.5 px-2 backdrop-blur-sm">
                      {item.catalog_id}
                    </span>
                  </div>
                  <div className="absolute bottom-2.5 right-2.5 font-mono text-[10px] bg-archive-charcoal/85 text-white px-2 py-0.5 rounded backdrop-blur-sm">
                    {item.confidence_score}% MATCH
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-4 space-y-2.5">
                  <div className="flex items-center justify-between font-mono text-[10px] text-archive-muted">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-archive-terracotta" />
                      {formatDate(item.timestamp)}
                    </span>
                    <span className="text-archive-stone font-semibold">
                      {item.verification_tier?.includes('TIER 1') ? 'TIER 1 (LOCAL)' : 'TIER 2 (VLM)'}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-serif text-xl font-bold text-archive-charcoal group-hover:text-archive-terracotta transition-colors">
                      {item.monument_name}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-archive-stone mt-0.5">
                      <MapPin className="w-3 h-3 text-archive-terracotta/70 flex-shrink-0" />
                      <span className="truncate">{item.location}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-archive-hairline/80 font-mono text-[11px] text-archive-muted flex items-center justify-between">
                    <span className="truncate">{item.architectural_style}</span>
                    <span className="text-archive-terracotta font-semibold text-[10px] flex items-center gap-1 flex-shrink-0">
                      View Dossier →
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Selected Scan Full Modal Dossier */}
      <AnimatePresence>
        {selectedScan && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-archive-charcoal/70 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 240, damping: 22 }}
              className="relative w-full max-w-5xl bg-archive-alabaster rounded-lg shadow-2xl p-4 sm:p-6 max-h-[90vh] overflow-y-auto my-8 border border-archive-hairline"
            >
              <div className="flex justify-between items-center pb-3 border-b border-archive-hairline mb-6">
                <div className="font-mono text-xs text-archive-terracotta tracking-stamp uppercase font-bold">
                  SURVEY LOG ARCHIVE SPECIMEN // {selectedScan.catalog_id}
                </div>
                <button
                  onClick={() => setSelectedScan(null)}
                  className="p-1.5 text-archive-stone hover:text-archive-charcoal bg-white rounded border border-archive-hairline hover:border-archive-borderDark transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <MonographResult
                result={{
                  is_monument: true,
                  verification_tier: selectedScan.verification_tier,
                  confidence_score: selectedScan.confidence_score,
                  catalog_id: selectedScan.catalog_id,
                  monument_name: selectedScan.monument_name,
                  monument_key: selectedScan.monument_key,
                  location: selectedScan.location,
                  coordinates: selectedScan.coordinates,
                  architectural_style: selectedScan.architectural_style,
                  built_by_or_era: selectedScan.built_by_or_era,
                  historical_summary: selectedScan.historical_summary,
                  structural_features_detected: selectedScan.structural_features_detected,
                  pipeline_telemetry: selectedScan.pipeline_telemetry,
                }}
                imagePreview={selectedScan.thumbnail}
                onReset={() => setSelectedScan(null)}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

