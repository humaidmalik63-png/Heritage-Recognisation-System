import React from 'react';
import { Landmark, AlertTriangle } from 'lucide-react';
import { DISPLAY_CATALOGUE_SIZE, DISPLAY_ANCHOR_COUNT } from '../constants/displayMetrics';

export default function MobileHeader({
  health,
  onOpenCatalog,
  monumentsCount = DISPLAY_CATALOGUE_SIZE,
  onOpenExceptions,
  pendingExceptionsCount = 0,
}) {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="sticky top-0 z-40 bg-[#F5F3ED]/95 backdrop-blur-md border-b border-[#E3DFD5]">
      {/* Archival metadata micro-ribbon */}
      <div className="bg-[#ECE8DD] px-3 py-1 border-b border-[#E3DFD5]/60 flex items-center justify-between text-[9px] font-mono tracking-wider text-[#6E7069]">
        <div className="flex items-center gap-1.5 truncate">
          <span className="w-1.5 h-1.5 rounded-full bg-[#A9472D] flex-shrink-0" />
          <span className="truncate uppercase font-medium">ASI & UNESCO REGISTER</span>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
            }`}
          />
          <span className="text-[#171816] font-semibold">
            {DISPLAY_ANCHOR_COUNT} VECTORS
          </span>
        </div>
      </div>

      {/* Main compact brand and control bar */}
      <div className="px-3.5 py-2.5 flex items-center justify-between gap-2">
        {/* Left: Brand Identity */}
        <div className="flex items-center gap-2">
          <span className="font-display font-extrabold text-base tracking-tight text-[#171816]">
            HERITAGE<span className="text-[#A9472D]">.</span>
          </span>
          <span className="hidden xs:inline-block px-1.5 py-0.5 rounded bg-[#FFFEFA] border border-[#E3DFD5] text-[9px] font-mono text-[#6E7069] uppercase">
            Mobile v2
          </span>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1.5">
          {/* Catalogue Quick Pill */}
          <button
            onClick={onOpenCatalog}
            className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#FFFEFA] border border-[#E3DFD5] hover:border-[#171816] text-[#171816] text-[10px] font-mono font-medium transition-colors shadow-2xs active:scale-95"
            title={`Open ${DISPLAY_CATALOGUE_SIZE} Canonical Monuments Catalogue`}
          >
            <Landmark className="w-3 h-3 text-[#B99A5B]" />
            <span>{DISPLAY_CATALOGUE_SIZE}</span>
          </button>

          {/* Exceptions / Human Review Pill */}
          {pendingExceptionsCount > 0 && (
            <button
              onClick={onOpenExceptions}
              className="flex items-center gap-1 px-2 py-1 rounded-lg bg-amber-50 border border-amber-300 text-amber-900 text-[10px] font-mono font-semibold transition-colors active:scale-95"
              title="Curatorial Human Review Exceptions"
            >
              <AlertTriangle className="w-3 h-3 text-amber-600" />
              <span>{pendingExceptionsCount}</span>
            </button>
          )}

          {/* Local-session badge (no sign-in in this app) */}
          <div
            className="w-7 h-7 rounded-full bg-[#171816] text-[#F5F3ED] flex items-center justify-center text-[10px] font-mono font-bold border border-[#E3DFD5]"
            title="Heritage — local session, no sign-in"
          >
            H
          </div>
        </div>
      </div>
    </header>
  );
}

