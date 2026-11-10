import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Public Access Transition:
 * The Heritage Recognition System is fully public; authentication redirects to the homepage.
 */
export default function Login() {
  return <Navigate to="/" replace />;
}
