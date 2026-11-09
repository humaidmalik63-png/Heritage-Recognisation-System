import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, Mail, ArrowRight, AlertCircle, KeyRound, ArrowLeft, Landmark } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError('Please provide both official email and security password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickDemoLogin = async () => {
    setError(null);
    setIsSubmitting(true);
    try {
      await login('curator@heritage.org', 'curator123');
      navigate(from, { replace: true });
    } catch (err) {
      setError('Could not initiate demo session.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden flex flex-col justify-between selection:bg-[#A9472D] selection:text-white">
      {/* 1. Cinematic Background Video & Layered Atmosphere */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <video
          autoPlay
          loop
          muted
          playsInline
          poster="/assets/heritage/taj-mahal.jpg"
          className="w-full h-full object-cover scale-105"
        >
          <source src="/assets/videos/heritage-ambient.mp4" type="video/mp4" />
        </video>

        {/* Cinematic Scrim & Vignette */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/55 to-black/75" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_0%,_rgba(0,0,0,0.6)_100%)]" />

        {/* Ambient Warm Architectural Light Glows */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-[#A9472D]/25 blur-[120px]" />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-[#B99A5B]/25 blur-[120px]" />

        {/* Procedural Film Grain Overlay */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none mix-blend-overlay"
          style={{ backgroundImage: 'url(/assets/grain.svg)', backgroundSize: 'cover' }}
        />
      </div>

      {/* 2. Top Archival Header Strip (Glassmorphism) */}
      <header className="relative z-20 bg-black/40 backdrop-blur-md border-b border-white/10 px-4 sm:px-8 py-3 text-[11px] font-mono text-white/80 flex justify-between items-center tracking-wider">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-semibold text-white uppercase tracking-widest">
            ARCHAEOLOGICAL SURVEY OF INDIA • CURATORIAL PORTAL
          </span>
        </div>

        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs text-white/70 hover:text-white transition-colors group"
        >
          <ArrowLeft className="w-3.5 h-3.5 transition-transform group-hover:-translate-x-1" />
          <span>Return to Discovery Platform</span>
        </Link>
      </header>

      {/* 3. Main Center Stage with POP UP Animation */}
      <main className="relative z-20 flex-1 flex items-center justify-center p-4 sm:p-6 my-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.85, y: 35 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{
            type: 'spring',
            stiffness: 280,
            damping: 22,
            mass: 0.85,
            delay: 0.05,
          }}
          className="w-full max-w-md bg-[#FFFEFA]/95 backdrop-blur-2xl border border-white/60 shadow-[0_30px_70px_-15px_rgba(0,0,0,0.6)] rounded-3xl p-6 sm:p-10"
        >
          {/* Card Masthead */}
          <div className="text-center pb-6 border-b border-[#E3DFD5]">
            <span className="font-mono text-[10px] uppercase text-[#A9472D] tracking-widest font-bold block mb-1">
              HERITAGE ACCESS CONTROL
            </span>
            <h1 className="font-serif text-3xl sm:text-4xl font-bold text-[#171816] tracking-tight">
              Curator Sign In
            </h1>
            <p className="mt-2 text-xs font-sans text-[#6E7069] leading-relaxed">
              Authenticate your credentials to access the Two-Tier Visual Vector Verification engine and personal archival scan log.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2 font-sans"
            >
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-[#171816] font-semibold mb-1.5">
                Official Email
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="curator@heritage.org"
                  className="w-full pl-9 pr-3 py-2.5 bg-white border border-[#E3DFD5] rounded-xl text-xs font-sans text-[#171816] placeholder:text-[#6E7069]/60 focus:outline-none focus:border-[#A9472D] focus:ring-1 focus:ring-[#A9472D] transition-all shadow-sm"
                  required
                />
                <Mail className="w-4 h-4 text-[#6E7069] absolute left-3 top-3 pointer-events-none" />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#171816] font-semibold">
                  Security Password
                </label>
                <span className="text-[10px] font-mono text-[#6E7069]">Demo: curator123</span>
              </div>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2.5 bg-white border border-[#E3DFD5] rounded-xl text-xs font-sans text-[#171816] placeholder:text-[#6E7069]/60 focus:outline-none focus:border-[#A9472D] focus:ring-1 focus:ring-[#A9472D] transition-all shadow-sm"
                  required
                />
                <Lock className="w-4 h-4 text-[#6E7069] absolute left-3 top-3 pointer-events-none" />
              </div>
            </div>

            <motion.button
              whileHover={{ y: -1, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-3 bg-[#171816] hover:bg-[#A9472D] text-white text-xs font-mono uppercase tracking-wider rounded-xl shadow-md transition-colors flex items-center justify-center gap-2 font-semibold cursor-pointer"
            >
              <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Register'}</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#B99A5B]" />
            </motion.button>
          </form>

          {/* Quick Demo Login Option */}
          <div className="mt-5 pt-4 border-t border-[#E3DFD5] text-center">
            <motion.button
              whileHover={{ y: -1, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              type="button"
              onClick={handleQuickDemoLogin}
              disabled={isSubmitting}
              className="w-full py-2.5 bg-white hover:bg-[#F5F3ED] text-[#171816] border border-[#E3DFD5] rounded-xl text-xs font-mono tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm cursor-pointer font-medium"
            >
              <KeyRound className="w-3.5 h-3.5 text-[#A9472D]" />
              <span>One-Click Curator Demo Login</span>
            </motion.button>
          </div>

          {/* Switch to Signup */}
          <div className="mt-6 text-center text-xs font-sans text-[#6E7069]">
            <span>New curatorial officer or field researcher? </span>
            <Link
              to="/signup"
              className="text-[#A9472D] font-semibold hover:underline font-mono"
            >
              Create Account
            </Link>
          </div>
        </motion.div>
      </main>

      {/* 4. Translucent Footer */}
      <footer className="relative z-20 py-3.5 text-center font-mono text-[10px] text-white/60 border-t border-white/10 bg-black/40 backdrop-blur-md">
        CENTRAL ARCHAEOLOGICAL REGISTRY • SECURED BY LOCAL VECTOR TOKENS • 2026 EDITION
      </footer>
    </div>
  );
}