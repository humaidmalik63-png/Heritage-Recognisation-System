import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import CatalogDrawer from './components/CatalogDrawer';
import ExceptionsDrawer from './components/ExceptionsDrawer';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Login from './pages/Login';
import Signup from './pages/Signup';
import { checkHealth, fetchMonumentsCatalog, fetchExceptions } from './api';

function AppLayout() {
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

  return (
    <div className="min-h-screen bg-archive-alabaster flex flex-col justify-between selection:bg-archive-terracotta selection:text-white">
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

      {/* Main Content Viewport */}
      <main className={!isAuthPage ? "flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8" : "flex-1"}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard onExceptionCreated={refreshPendingCount} />
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

      {/* Museum Masthead Footer */}
      {!isAuthPage && (
        <footer className="bg-archive-ivory border-t border-archive-hairline mt-12 py-7 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-archive-muted gap-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-archive-terracotta"></span>
              <span>HERITAGE & MONUMENT ARCHIVAL SYSTEM • ASI REGISTER • 2026 EDITION</span>
            </div>
            <div>
              AUTHENTICATION & PERSISTENCE ENGINE • REACT 19 + VITE + TAILWIND + FAISS
            </div>
          </div>
        </footer>
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
