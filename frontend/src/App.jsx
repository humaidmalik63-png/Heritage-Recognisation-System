import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import HeritageFooter from './components/HeritageFooter';
import MobileBottomNav from './components/MobileBottomNav';
import useIsMobile from './hooks/useIsMobile';
import { checkHealth, fetchMonumentsCatalog, fetchExceptions } from './api';

// Code-split dynamic routes and non-critical drawer overlays
const Dashboard = lazy(() => import('./pages/Dashboard'));
const History = lazy(() => import('./pages/History'));
const MobileApp = lazy(() => import('./mobile/MobileApp'));
const CatalogDrawer = lazy(() => import('./components/CatalogDrawer'));
const ExceptionsDrawer = lazy(() => import('./components/ExceptionsDrawer'));

function ArchivalLoadingFallback() {
  return (
    <div className="min-h-[50vh] bg-transparent flex items-center justify-center p-8 text-[#171816]">
      <div className="flex flex-col items-center gap-3">
        <div className="w-7 h-7 rounded-full border-2 border-[#E3DFD5] border-t-[#A9472D] animate-spin" />
        <span className="font-mono text-[10px] uppercase tracking-wider text-[#6E7069]">
          Accessing Archival Registry...
        </span>
      </div>
    </div>
  );
}

function AppLayout() {
  const isMobile = useIsMobile(768);
  const [health, setHealth] = useState(null);
  const [monuments, setMonuments] = useState({});
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [isExceptionsOpen, setIsExceptionsOpen] = useState(false);
  const [pendingExceptionsCount, setPendingExceptionsCount] = useState(0);
  const location = useLocation();

  const refreshPendingCount = async () => {
    try {
      const data = await fetchExceptions();
      if (Array.isArray(data)) {
        const pending = data.filter((e) => e.status === 'PENDING_REVIEW').length;
        setPendingExceptionsCount(pending);
      }
    } catch {
      // Backend may be starting up
    }
  };

  useEffect(() => {
    async function init() {
      try {
        const healthData = await checkHealth();
        setHealth(healthData);
      } catch (err) {
        console.warn('Backend connecting or starting up:', err.message);
      }

      try {
        const catalogData = await fetchMonumentsCatalog();
        if (catalogData && catalogData.monuments) {
          setMonuments(catalogData.monuments);
        }
      } catch (err) {
        console.warn('Could not fetch catalog:', err.message);
      }

      refreshPendingCount();
    }
    init();
  }, []);

  // Separate Mobile Frontend Experience (Active on < 768px viewports) - Completely Public Entry
  if (isMobile) {
    return (
      <Suspense fallback={<ArchivalLoadingFallback />}>
        <MobileApp
          health={health}
          monuments={monuments}
          onOpenCatalog={() => setIsCatalogOpen(true)}
          onOpenExceptions={() => setIsExceptionsOpen(true)}
          pendingExceptionsCount={pendingExceptionsCount}
        />

        {/* Global Catalog Drawer */}
        {isCatalogOpen && (
          <CatalogDrawer
            isOpen={isCatalogOpen}
            onClose={() => setIsCatalogOpen(false)}
            monuments={monuments}
          />
        )}

        {/* Human Review Exceptions Drawer */}
        {isExceptionsOpen && (
          <ExceptionsDrawer
            isOpen={isExceptionsOpen}
            onClose={() => {
              setIsExceptionsOpen(false);
              refreshPendingCount();
            }}
            onCountChange={(cnt) => setPendingExceptionsCount(cnt)}
          />
        )}
      </Suspense>
    );
  }

  return (
    <div className="min-h-screen bg-archive-alabaster flex flex-col justify-between selection:bg-archive-terracotta selection:text-white">
      {/* Main Header (Rendered on all public views) */}
      <Header
        health={health}
        onOpenCatalog={() => setIsCatalogOpen(true)}
        monumentsCount={Object.keys(monuments).length}
        onOpenExceptions={() => setIsExceptionsOpen(true)}
        pendingExceptionsCount={pendingExceptionsCount}
      />

      {/* Main Content Viewport with mobile bottom nav safe-clearance */}
      <main className={location.pathname === '/' ? "flex-1 w-full pb-20 lg:pb-0" : "flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 pb-24 lg:pb-8"}>
        <Suspense fallback={<ArchivalLoadingFallback />}>
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  onExceptionCreated={refreshPendingCount}
                  monuments={monuments}
                  health={health}
                  onOpenCatalog={() => setIsCatalogOpen(true)}
                />
              }
            />
            <Route
              path="/history"
              element={<History />}
            />
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="/signup" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>

      {/* Institutional Editorial Footer */}
      <HeritageFooter
        onOpenCatalog={() => setIsCatalogOpen(true)}
        onOpenExceptions={() => setIsExceptionsOpen(true)}
      />

      {/* Mobile Fixed Bottom Navigation Bar (Hidden on desktop) */}
      <MobileBottomNav
        onRecognizeClick={() => {
          const el = document.getElementById('recognition');
          if (el) el.scrollIntoView({ behavior: 'smooth' });
        }}
        onOpenCatalog={() => setIsCatalogOpen(true)}
      />

      {/* Global Catalog Drawer (Mounted on demand) */}
      {isCatalogOpen && (
        <Suspense fallback={null}>
          <CatalogDrawer
            isOpen={isCatalogOpen}
            onClose={() => setIsCatalogOpen(false)}
            monuments={monuments}
          />
        </Suspense>
      )}

      {/* Human Review Exceptions Drawer (Mounted on demand) */}
      {isExceptionsOpen && (
        <Suspense fallback={null}>
          <ExceptionsDrawer
            isOpen={isExceptionsOpen}
            onClose={() => {
              setIsExceptionsOpen(false);
              refreshPendingCount();
            }}
            onCountChange={(cnt) => setPendingExceptionsCount(cnt)}
          />
        </Suspense>
      )}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  );
}
