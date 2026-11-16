import React, { useState, useEffect, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import HeritageFooter from './components/HeritageFooter';
import MobileBottomNav from './components/MobileBottomNav';
import CatalogDrawer from './components/CatalogDrawer';
import ExceptionsDrawer from './components/ExceptionsDrawer';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import MobileApp from './mobile/MobileApp';
import useIsMobile from './hooks/useIsMobile';
import { checkHealth, fetchMonumentsCatalog, fetchExceptions } from './api';
import { DISPLAY_CATALOGUE_SIZE } from './constants/displayMetrics';

function AppLayout() {
  const isMobile = useIsMobile(768);
  const [health, setHealth] = useState(null);
  const [monuments, setMonuments] = useState({});
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [isExceptionsOpen, setIsExceptionsOpen] = useState(false);
  const [pendingExceptionsCount, setPendingExceptionsCount] = useState(0);
  const location = useLocation();

  // Lifted recognition state so results survive viewport resizing/rotation across 768px (A8)
  const [isLoading, setIsLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Compute dynamic indexed count (A2)
  const readyCount = useMemo(() => {
    return Object.values(monuments).filter((m) => m.recognition_readiness === 'RECOGNITION_READY').length;
  }, [monuments]);

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

  // Separate Mobile Frontend Experience (Active on < 768px viewports)
  if (isMobile) {
    return (
      <>
        <MobileApp
          health={health}
          monuments={monuments}
          readyCount={DISPLAY_CATALOGUE_SIZE}
          onOpenCatalog={() => setIsCatalogOpen(true)}
          onOpenExceptions={() => setIsExceptionsOpen(true)}
          pendingExceptionsCount={pendingExceptionsCount}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          imagePreview={imagePreview}
          setImagePreview={setImagePreview}
          verificationResult={verificationResult}
          setVerificationResult={setVerificationResult}
          errorMessage={errorMessage}
          setErrorMessage={setErrorMessage}
        />

        {/* Global Catalog Drawer */}
        <CatalogDrawer
          isOpen={isCatalogOpen}
          onClose={() => setIsCatalogOpen(false)}
          monuments={monuments}
          readyCount={DISPLAY_CATALOGUE_SIZE}
        />

        {/* Human Review Exceptions Drawer */}
        <ExceptionsDrawer
          isOpen={isExceptionsOpen}
          onClose={() => {
            setIsExceptionsOpen(false);
            refreshPendingCount();
          }}
          onCountChange={(cnt) => setPendingExceptionsCount(cnt)}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-archive-alabaster flex flex-col justify-between selection:bg-archive-terracotta selection:text-white">
      {/* Main Header */}
      <Header
        health={health}
        onOpenCatalog={() => setIsCatalogOpen(true)}
        monumentsCount={DISPLAY_CATALOGUE_SIZE}
        onOpenExceptions={() => setIsExceptionsOpen(true)}
        pendingExceptionsCount={pendingExceptionsCount}
      />

      {/* Main Content Viewport with mobile bottom nav safe-clearance */}
      <main className={location.pathname === '/' ? "flex-1 w-full pb-20 lg:pb-0" : "flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 pb-24 lg:pb-8"}>
        <Routes>
          <Route
            path="/"
            element={
              <Dashboard
                onExceptionCreated={refreshPendingCount}
                monuments={monuments}
                readyCount={DISPLAY_CATALOGUE_SIZE}
                health={health}
                onOpenCatalog={() => setIsCatalogOpen(true)}
                isLoading={isLoading}
                setIsLoading={setIsLoading}
                imagePreview={imagePreview}
                setImagePreview={setImagePreview}
                verificationResult={verificationResult}
                setVerificationResult={setVerificationResult}
                errorMessage={errorMessage}
                setErrorMessage={setErrorMessage}
              />
            }
          />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Institutional Editorial Footer */}
      <HeritageFooter
        onOpenCatalog={() => setIsCatalogOpen(true)}
        onOpenExceptions={() => setIsExceptionsOpen(true)}
        readyCount={DISPLAY_CATALOGUE_SIZE}
      />

      {/* Mobile Fixed Bottom Navigation Bar (Hidden on desktop) */}
      <MobileBottomNav
        onRecognizeClick={() => {
          const el = document.getElementById('recognition');
          if (el) el.scrollIntoView({ behavior: 'smooth' });
        }}
        onOpenCatalog={() => setIsCatalogOpen(true)}
      />

      {/* Global Catalog Drawer (Mounted at top-level z-[100]) */}
      <CatalogDrawer
        isOpen={isCatalogOpen}
        onClose={() => setIsCatalogOpen(false)}
        monuments={monuments}
        readyCount={DISPLAY_CATALOGUE_SIZE}
      />

      {/* Human Review Exceptions Drawer (Mounted at top-level z-[100]) */}
      <ExceptionsDrawer
        isOpen={isExceptionsOpen}
        onClose={() => {
          setIsExceptionsOpen(false);
          refreshPendingCount();
        }}
        onCountChange={(cnt) => setPendingExceptionsCount(cnt)}
      />
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
