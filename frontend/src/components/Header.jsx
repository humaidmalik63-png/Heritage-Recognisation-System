import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import {
  BookOpen,
  ShieldCheck,
  ShieldAlert,
  History,
  ScanLine,
  LogOut,
  User as UserIcon,
  ChevronDown
} from 'lucide-react';

export default function Header({
  health,
  onOpenCatalog,
  monumentsCount,
  onOpenExceptions,
  pendingExceptionsCount = 0,
}) {
  const { user, logout, history } = useAuth();
  const location = useLocation();
  const isOnline = Boolean(health);

  const isScannerActive = location.pathname === '/';
  const isHistoryActive = location.pathname === '/history';

  return (
    <header className="bg-archive-ivory border-b border-archive-hairline shadow-sm sticky top-0 z-30 liquid-glass">
      {/* Micro Archival Classification Band */}
      <div className="bg-archive-parchment/60 border-b border-archive-hairline/80 px-4 sm:px-6 py-1.5 text-[11px] font-mono text-archive-stone flex flex-wrap justify-between items-center tracking-wider">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-medium text-archive-charcoal">
            <ShieldCheck className="w-3.5 h-3.5 text-archive-terracotta flex-shrink-0" />
            DIRECTORATE OF ARCHAEOLOGY & VLM RESEARCH
          </span>
          <span className="hidden sm:inline text-archive-hairline">•</span>
          <span className="hidden sm:inline text-[10px]">SERIES 2026-IND-HYBRID // SIH25052</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              {isOnline && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  isOnline ? 'bg-emerald-600' : 'bg-amber-600'
                }`}
              ></span>
            </span>
            <span className="text-[10px] uppercase font-mono">
              {isOnline
                ? `ENGINE ONLINE (${health.clip_device?.toUpperCase()})`
                : 'ENGINE CONNECTING...'}
            </span>
          </div>

          {health && (
            <span className="hidden md:inline font-mono text-archive-charcoal bg-white/80 px-2 py-0.5 border border-archive-hairline rounded text-[10px]">
              {health.faiss_vectors_loaded} VECTOR ANCHORS
            </span>
          )}
        </div>
      </div>

      {/* Main Masthead Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5 md:py-7">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-4 double-border-bottom">
          <div className="space-y-1">
            <div className="font-mono text-[10px] uppercase tracking-stamp text-archive-terracotta font-bold flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-archive-terracotta"></span>
              ARCHIVAL REGISTER // INDIAN HERITAGE & MONUMENT VERIFICATION
            </div>
            <Link to="/" className="inline-block">
              <h1 className="font-serif text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-archive-charcoal leading-none hover:text-archive-terracotta transition-colors">
                Indian Heritage & Monument Register
              </h1>
            </Link>
            <p className="pt-0.5 text-xs text-archive-stone font-sans max-w-2xl leading-relaxed">
              Two-Tier Hybrid Architecture integrating on-device CLIP (ViT-B/32) & FAISS Inner-Product vector indexing with Gemini 2.5 Flash VLM Deep Archaeological Fallback.
            </p>
          </div>

          {/* Navigation & User Profile */}
          <div className="flex flex-wrap items-center gap-2.5 self-start md:self-end flex-shrink-0">
            {/* Nav: Scanner */}
            <Link to="/">
              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono uppercase tracking-wider transition-colors shadow-sm border ${
                  isScannerActive
                    ? 'bg-archive-charcoal text-white border-archive-charcoal'
                    : 'bg-white hover:bg-archive-alabaster text-archive-charcoal border-archive-hairline'
                }`}
              >
                <ScanLine className="w-3.5 h-3.5 text-archive-terracotta" />
                <span>Scanner</span>
              </motion.button>
            </Link>

            {/* Nav: History */}
            <Link to="/history">
              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono uppercase tracking-wider transition-colors shadow-sm border ${
                  isHistoryActive
                    ? 'bg-archive-charcoal text-white border-archive-charcoal'
                    : 'bg-white hover:bg-archive-alabaster text-archive-charcoal border-archive-hairline'
                }`}
              >
                <History className="w-3.5 h-3.5 text-archive-terracotta" />
                <span>Archival Log</span>
                {history.length > 0 && (
                  <span className="ml-0.5 px-1.5 py-0.2 bg-archive-terracotta text-white rounded-full text-[10px] font-bold">
                    {history.length}
                  </span>
                )}
              </motion.button>
            </Link>

            {/* Nav: Monument Catalog Drawer */}
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onOpenCatalog}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-archive-parchment/60 text-archive-charcoal border border-archive-hairline hover:border-archive-borderDark rounded text-xs font-mono uppercase tracking-wider transition-colors shadow-sm"
            >
              <BookOpen className="w-3.5 h-3.5 text-archive-terracotta" />
              <span>Catalog ({monumentsCount || 10})</span>
            </motion.button>

            {/* Nav: Human Review Exceptions Drawer */}
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onOpenExceptions}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-amber-50 text-archive-charcoal border border-archive-hairline hover:border-amber-300 rounded text-xs font-mono uppercase tracking-wider transition-colors shadow-sm"
              title="Curator Review Exception Log"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              <span>Exceptions</span>
              {pendingExceptionsCount > 0 && (
                <span className="ml-0.5 px-1.5 py-0.2 bg-amber-600 text-white rounded-full text-[10px] font-bold animate-pulse">
                  {pendingExceptionsCount}
                </span>
              )}
            </motion.button>

            {/* User Profile Badge & Logout */}
            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-archive-hairline/80">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="font-serif font-bold text-xs text-archive-charcoal leading-tight">
                    {user.name}
                  </span>
                  <span className="font-mono text-[9px] text-archive-terracotta leading-tight">
                    {user.badgeNumber || 'FELLOW'}
                  </span>
                </div>

                <div className="w-7 h-7 rounded-full bg-archive-terracotta/10 border border-archive-terracotta/30 flex items-center justify-center font-mono text-xs font-bold text-archive-terracotta shadow-inner">
                  {user.name?.charAt(0) || 'U'}
                </div>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={logout}
                  className="p-1.5 text-archive-stone hover:text-rose-700 hover:bg-rose-50 rounded border border-transparent hover:border-rose-200 transition-colors"
                  title="Sign Out of Session"
                  aria-label="Logout"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </motion.button>
              </div>
            ) : (
              <Link to="/login" className="pl-2 border-l border-archive-hairline/80">
                <motion.button
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-3 py-1.5 bg-archive-terracotta text-white rounded text-xs font-mono uppercase tracking-wider shadow-sm hover:bg-archive-terracottaDark transition-colors"
                >
                  Sign In
                </motion.button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
