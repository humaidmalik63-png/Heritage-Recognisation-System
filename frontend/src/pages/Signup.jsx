import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Public Access Transition:
 * The Heritage Recognition System is fully public; registration redirects to the homepage.
 */
export default function Signup() {
  return <Navigate to="/" replace />;
}
