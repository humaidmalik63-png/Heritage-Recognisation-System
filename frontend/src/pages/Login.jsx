import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, Mail, ArrowRight, AlertCircle, KeyRound, Sparkles } from 'lucide-react';

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
    <div className="min-h-screen bg-archive-alabaster flex flex-col justify-between selection:bg-archive-terracotta selection:text-white">
      {/* Top Archival Header Strip */}
      <div className="bg-archive-parchment/60 border-b border-archive-hairline px-4 sm:px-6 py-2 text-[11px] font-mono text-archive-stone flex justify-between items-center tracking-wider">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-archive-terracotta" />
          <span className="font-semibold text-archive-charcoal uppercase">
            ARCHAEOLOGICAL SURVEY OF INDIA • CURATORIAL PORTAL
          </span>
        </div>
        <span className="hidden sm:inline font-mono text-[10px] text-archive-muted">
          SESSION GATEWAY // SYSTEM ACCESS
        </span>
      </div>

      {/* Main Authentication Card */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-6 my-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 220, damping: 22 }}
          className="w-full max-w-md bg-archive-ivory border border-archive-hairline rounded shadow-plate p-6 sm:p-10 liquid-glass"
        >
          {/* Card Masthead */}
          <div className="text-center pb-6 border-b border-archive-hairline">
            <span className="font-mono text-[10px] uppercase text-archive-terracotta tracking-stamp font-bold block mb-1">
              HERITAGE ACCESS CONTROL
            </span>
            <h1 className="font-serif text-3xl sm:text-4xl font-bold text-archive-charcoal tracking-tight">
              Curator Sign In
            </h1>
            <p className="mt-2 text-xs font-sans text-archive-stone leading-relaxed">
              Authenticate your credentials to access the Two-Tier Visual Vector Verification engine and personal archival scan log.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-4 p-3 rounded bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2 font-sans"
            >
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-archive-charcoal font-semibold mb-1.5">
                Official Email
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="curator@heritage.org"
                  className="w-full pl-9 pr-3 py-2 bg-white border border-archive-hairline rounded text-xs font-sans text-archive-charcoal placeholder-archive-muted/60 focus:outline-none focus:border-archive-terracotta focus:ring-1 focus:ring-archive-terracotta transition-colors shadow-inner"
                  required
                />
                <Mail className="w-4 h-4 text-archive-muted absolute left-3 top-2.5 pointer-events-none" />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-archive-charcoal font-semibold">
                  Security Password
                </label>
                <span className="text-[10px] font-mono text-archive-muted">Demo: curator123</span>
              </div>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 bg-white border border-archive-hairline rounded text-xs font-sans text-archive-charcoal placeholder-archive-muted/60 focus:outline-none focus:border-archive-terracotta focus:ring-1 focus:ring-archive-terracotta transition-colors shadow-inner"
                  required
                />
                <Lock className="w-4 h-4 text-archive-muted absolute left-3 top-2.5 pointer-events-none" />
              </div>
            </div>

            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-2.5 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow transition-colors flex items-center justify-center gap-2 font-medium"
            >
              <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Register'}</span>
              <ArrowRight className="w-3.5 h-3.5 text-archive-parchment" />
            </motion.button>
          </form>

          {/* Quick Demo Login Option */}
          <div className="mt-5 pt-4 border-t border-archive-hairline text-center">
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              type="button"
              onClick={handleQuickDemoLogin}
              disabled={isSubmitting}
              className="w-full py-2 bg-white hover:bg-archive-alabaster text-archive-stone hover:text-archive-charcoal border border-archive-hairline rounded text-xs font-mono tracking-wider transition-colors flex items-center justify-center gap-2 shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5 text-archive-gold" />
              <span>One-Click Curator Demo Login</span>
            </motion.button>
          </div>

          {/* Switch to Signup */}
          <div className="mt-6 text-center text-xs font-sans text-archive-stone">
            <span>New curatorial officer or field researcher? </span>
            <Link
              to="/signup"
              className="text-archive-terracotta font-semibold hover:underline font-mono"
            >
              Create Account
            </Link>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center font-mono text-[10px] text-archive-muted border-t border-archive-hairline bg-archive-ivory">
        CENTRAL ARCHAEOLOGICAL REGISTRY • SECURED BY LOCAL VECTOR TOKENS
      </footer>
    </div>
  );
}

