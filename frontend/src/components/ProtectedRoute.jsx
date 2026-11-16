import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

export default function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-archive-alabaster flex flex-col items-center justify-center font-mono text-xs text-archive-stone space-y-3">
        <Loader2 className="w-6 h-6 text-archive-terracotta animate-spin" />
        <span className="tracking-stamp uppercase">VALIDATING ARCHIVAL CREDENTIALS...</span>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

