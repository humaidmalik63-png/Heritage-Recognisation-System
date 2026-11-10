import React from 'react';

/**
 * Transparent pass-through component for open cultural heritage access.
 * Eliminates login redirects while preserving component hierarchy compatibility.
 */
export default function ProtectedRoute({ children }) {
  return children;
}

