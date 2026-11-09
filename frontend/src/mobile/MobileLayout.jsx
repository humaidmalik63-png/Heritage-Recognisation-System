import React from 'react';
import MobileHeader from './MobileHeader';
import MobileBottomNav from './MobileBottomNav';
import './mobile.css';

export default function MobileLayout({
  health,
  onOpenCatalog,
  monumentsCount = 100,
  onOpenExceptions,
  pendingExceptionsCount = 0,
  activeTab,
  onSelectTab,
  children,
}) {
  return (
    <div className="min-h-screen bg-[#F5F3ED] text-[#171816] flex flex-col font-sans selection:bg-[#A9472D] selection:text-white">
      {/* Mobile Sticky Header */}
      <MobileHeader
        health={health}
        onOpenCatalog={onOpenCatalog}
        monumentsCount={monumentsCount}
        onOpenExceptions={onOpenExceptions}
        pendingExceptionsCount={pendingExceptionsCount}
      />

      {/* Main Scrollable View Area (pb-24 gives plenty of room above the bottom navigation bar) */}
      <main className="flex-1 w-full max-w-lg mx-auto px-4 py-3 pb-24">
        {children}
      </main>

      {/* Fixed Bottom Navigation Bar */}
      <MobileBottomNav
        activeTab={activeTab}
        onSelectTab={onSelectTab}
      />
    </div>
  );
}

