import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import HeritageFooter from './components/HeritageFooter';
import MobileBottomNav from './components/MobileBottomNav';
import CatalogDrawer from './components/CatalogDrawer';
import ExceptionsDrawer from './components/ExceptionsDrawer';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Login from './pages/Login';
import Signup from './pages/Signup';
import MobileApp from './mobile/MobileApp';
import useIsMobile from './hooks/useIsMobile';
import { checkHealth, fetchMonumentsCatalog, fetchExceptions } from './api';

function AppLayout() {
  const isMobile = useIsMobile(768);
  const [health, setHealth] = useState(null);
  const [monuments, setMonuments] = useState({});
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [isExceptionsOpen, setIsExceptionsOpen] = useState(false);
  const [pendingExceptionsCount, setPendingExceptionsCount] = useState(0);
  const location = useLocation();

  const isAuthPage = location.pathname === '/login' || location.pathname === '/signup';

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
  if (isMobile && !isAuthPage) {
    return (
      <ProtectedRoute>
        <MobileApp
          health={health}
          monuments={monuments}
          onOpenCatalog={() => setIsCatalogOpen(true)}
          onOpenExceptions={() => setIsExceptionsOpen(true)}
          pendingExceptionsCount={pendingExceptionsCount}
        />

        {/* Global Catalog Drawer */}
        <CatalogDrawer
          isOpen={isCatalogOpen}
          onClose={() => setIsCatalogOpen(false)}
          monuments={monuments}
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
      </ProtectedRoute>
    );
  }

  return (
    <div className="min-h-screen bg-archive-alabaster flex flex-col justify-between selection:bg-archive-terracotta selection:text-white">
      {/* Main Header (Rendered on protected views) */}
      {!isAuthPage && (
        <Header
          health={health}
          onOpenCatalog={() => setIsCatalogOpen(true)}
          monumentsCount={Object.keys(monuments).length}
          onOpenExceptions={() => setIsExceptionsOpen(true)}
          pendingExceptionsCount={pendingExceptionsCount}
        />
      )}

      {/* Main Content Viewport with mobile bottom nav safe-clearance */}
      <main className={!isAuthPage ? (location.pathname === '/' ? "flex-1 w-full pb-20 lg:pb-0" : "flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 pb-24 lg:pb-8") : "flex-1"}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard
                  onExceptionCreated={refreshPendingCount}
                  monuments={monuments}
                  health={health}
                  onOpenCatalog={() => setIsCatalogOpen(true)}
                />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Institutional Editorial Footer */}
      {!isAuthPage && (
        <HeritageFooter
          onOpenCatalog={() => setIsCatalogOpen(true)}
          onOpenExceptions={() => setIsExceptionsOpen(true)}
        />
      )}

      {/* Mobile Fixed Bottom Navigation Bar (Hidden on desktop) */}
      {!isAuthPage && (
        <MobileBottomNav
          onRecognizeClick={() => {
            const el = document.getElementById('recognition');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }}
          onOpenCatalog={() => setIsCatalogOpen(true)}
        />
      )}

      {/* Global Catalog Drawer (Mounted at top-level z-[100]) */}
      <CatalogDrawer
        isOpen={isCatalogOpen}
        onClose={() => setIsCatalogOpen(false)}
        monuments={monuments}
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
