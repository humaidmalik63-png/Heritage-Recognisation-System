import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import {
  BookOpen,
  ShieldAlert,
  History,
  ScanLine,
  LogOut,
  Menu,
  X,
} from 'lucide-react';

export default function Header({
  health,
  onOpenCatalog,
  monumentsCount = 100,
  onOpenExceptions,
  pendingExceptionsCount = 0,
}) {
  const { user, logout, history } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isHomePage = location.pathname === '/';
  const isOnline = Boolean(health);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id) => {
    setMobileMenuOpen(false);
    if (!isHomePage) {
      navigate(`/#${id}`);
      setTimeout(() => {
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      return;
    }

    if (id === 'top') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="sticky top-0 z-40 px-3 sm:px-6 pt-2 pb-1.5 transition-all duration-300">
      <div
        className={`max-w-[1360px] mx-auto rounded-2xl transition-all duration-300 ${
          isScrolled
            ? 'bg-[#FFFEFA]/95 backdrop-blur-md shadow-md border border-[#E3DFD5]'
            : 'bg-[#FFFEFA] shadow-sm border border-[#E3DFD5]'
        }`}
      >
        {/* Top Archival Ribbon (Minimal & Institutional) */}
        <div className="px-5 sm:px-6 py-1.5 border-b border-[#E3DFD5]/70 flex flex-wrap justify-between items-center text-[10px] font-mono tracking-wider text-[#6E7069]">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#A9472D]" />
            <span className="font-semibold text-[#171816] uppercase tracking-widest">
              ASI & UNESCO REGISTER
            </span>
            <span className="hidden sm:inline text-[#E3DFD5]">|</span>
            <span className="hidden sm:inline text-[#6E7069] uppercase">
              Multimodal Epigraphy Series 2026
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-emerald-500'
                }`}
              />
              <span className="uppercase text-[10px] font-mono text-[#171816] font-medium">
                {isOnline
                  ? `Engine Online (${health.clip_device?.toUpperCase() || 'CPU'})`
                  : 'Engine Online (CPU)'}
              </span>
            </div>

            <span className="hidden md:inline-flex items-center gap-1 text-[#6E7069] text-[10px] font-mono border-l border-[#E3DFD5] pl-2.5">
              <span>{health?.faiss_vectors_loaded || 577} Vectors</span>
              <span>•</span>
              <span>{monumentsCount || 100} Sites</span>
            </span>
          </div>
        </div>

        {/* Main Navigation Bar */}
        <div className="px-5 sm:px-6 py-2.5 sm:py-3 flex items-center justify-between gap-4">
          {/* Brand Logo */}
          <Link
            to="/"
            onClick={() => scrollToSection('top')}
            className="group flex items-baseline gap-2.5 flex-shrink-0"
          >
            <span className="font-serif text-2xl sm:text-[26px] font-bold tracking-tight text-[#171816] group-hover:text-[#A9472D] transition-colors leading-none">
              HERITAGE<span className="text-[#A9472D]">.</span>
            </span>
            <span className="hidden md:inline-block font-mono text-[9px] uppercase tracking-widest text-[#6E7069] pl-2.5 border-l border-[#E3DFD5]">
              Curatorial Archive
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <nav
            className="hidden lg:flex items-center gap-6 xl:gap-8 text-[13px] font-sans font-medium text-[#171816]"
            aria-label="Main navigation"
          >
            <button
              onClick={() => scrollToSection('discover')}
              className="text-[#171816]/75 hover:text-[#A9472D] transition-colors cursor-pointer py-1 whitespace-nowrap"
            >
              Discover
            </button>
            <button
              onClick={() => scrollToSection('archive')}
              className="text-[#171816]/75 hover:text-[#A9472D] transition-colors cursor-pointer py-1 whitespace-nowrap"
            >
              Archive
            </button>
            <button
              onClick={() => scrollToSection('recognition')}
              className="text-[#171816]/75 hover:text-[#A9472D] transition-colors cursor-pointer py-1 whitespace-nowrap"
            >
              Recognition
            </button>
            <button
              onClick={() => scrollToSection('how-it-works')}
              className="text-[#171816]/75 hover:text-[#A9472D] transition-colors cursor-pointer py-1 whitespace-nowrap"
            >
              How It Works
            </button>
            <button
              onClick={() => scrollToSection('about')}
              className="text-[#171816]/75 hover:text-[#A9472D] transition-colors cursor-pointer py-1 whitespace-nowrap"
            >
              About
            </button>
          </nav>

          {/* Right Action Suite */}
          <div className="flex items-center gap-2.5 sm:gap-3 flex-shrink-0">
            {/* Unified Curatorial Tools Segmented Pill */}
            <div className="hidden xl:inline-flex items-center rounded-full bg-[#F5F3ED] border border-[#E3DFD5] p-1 text-[11px] font-mono shadow-inner">
              {/* Catalogue Trigger */}
              <button
                onClick={onOpenCatalog}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full hover:bg-white text-[#171816] transition-all cursor-pointer font-medium"
                title="Open Complete 100-Site Catalogue Drawer"
              >
                <BookOpen className="w-3 h-3 text-[#A9472D]" />
                <span className="uppercase">Catalogue</span>
                <span className="font-bold text-[#A9472D] bg-[#A9472D]/10 px-1.5 py-0.2 rounded-full text-[10px]">
                  {monumentsCount || 100}
                </span>
              </button>

              <span className="w-px h-3.5 bg-[#E3DFD5]/80 mx-0.5" />

              {/* Review Exceptions Trigger */}
              <button
                onClick={onOpenExceptions}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full hover:bg-white text-[#171816] transition-all cursor-pointer font-medium"
                title="Curator Review Exception Log"
              >
                <ShieldAlert className="w-3 h-3 text-amber-600" />
                <span className="uppercase">Review</span>
                {pendingExceptionsCount > 0 && (
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-pulse" />
                )}
              </button>

              <span className="w-px h-3.5 bg-[#E3DFD5]/80 mx-0.5" />

              {/* Inspection History Trigger */}
              <Link
                to="/history"
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full hover:bg-white text-[#171816] transition-all cursor-pointer font-medium"
                title="View Personal Archival Survey Log"
              >
                <History className="w-3 h-3 text-[#B99A5B]" />
                <span className="uppercase">Log</span>
                <span className="text-[#6E7069] text-[10px]">({history.length})</span>
              </Link>
            </div>

            {/* Primary Action Button: Recognise a Monument */}
            <button
              onClick={() => scrollToSection('recognition')}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#A9472D] hover:bg-[#8A3720] text-white rounded-full text-xs sm:text-[13px] font-sans font-semibold tracking-wide shadow-sm hover:shadow-md transition-all cursor-pointer whitespace-nowrap flex-shrink-0"
            >
              <ScanLine className="w-3.5 h-3.5 text-[#B99A5B]" />
              <span className="whitespace-nowrap">Recognise a Monument</span>
            </button>

            {/* User Session Profile */}
            {user ? (
              <div className="hidden sm:flex items-center gap-1.5 pl-2 border-l border-[#E3DFD5]">
                <div
                  className="w-7 h-7 rounded-full bg-[#171816] text-[#F5F3ED] flex items-center justify-center font-mono text-[11px] font-bold shadow-sm"
                  title={user.name || user.email}
                >
                  {user.name?.charAt(0) || 'C'}
                </div>
                <button
                  onClick={logout}
                  className="p-1.5 text-[#6E7069] hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                  title="Sign Out of Session"
                  aria-label="Logout"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <Link to="/login" className="hidden sm:inline-block pl-2 border-l border-[#E3DFD5]">
                <span className="text-xs font-mono uppercase tracking-wider text-[#6E7069] hover:text-[#171816] transition-colors">
                  Sign In
                </span>
              </Link>
            )}

            {/* Mobile Hamburger Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl border border-[#E3DFD5] bg-[#F5F3ED] text-[#171816] cursor-pointer"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4 text-[#171816]" />}
            </button>
          </div>
        </div>

        {/* Mobile Accordion Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden px-4 pb-4 pt-2 border-t border-[#E3DFD5] space-y-3"
            >
              <div className="grid grid-cols-2 gap-2 text-xs font-mono uppercase">
                <button
                  onClick={() => scrollToSection('discover')}
                  className="p-2.5 text-left bg-[#F5F3ED] rounded-xl border border-[#E3DFD5] hover:bg-[#FFFEFA]"
                >
                  Discover
                </button>
                <button
                  onClick={() => scrollToSection('archive')}
                  className="p-2.5 text-left bg-[#F5F3ED] rounded-xl border border-[#E3DFD5] hover:bg-[#FFFEFA]"
                >
                  Archive
                </button>
                <button
                  onClick={() => scrollToSection('recognition')}
                  className="p-2.5 text-left bg-[#F5F3ED] rounded-xl border border-[#E3DFD5] hover:bg-[#FFFEFA]"
                >
                  Recognition
                </button>
                <button
                  onClick={() => scrollToSection('how-it-works')}
                  className="p-2.5 text-left bg-[#F5F3ED] rounded-xl border border-[#E3DFD5] hover:bg-[#FFFEFA]"
                >
                  How It Works
                </button>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenCatalog();
                  }}
                  className="p-2.5 text-left bg-[#F5F3ED] rounded-xl border border-[#E3DFD5] hover:bg-[#FFFEFA] flex items-center justify-between"
                >
                  <span>Catalogue</span>
                  <span className="text-[#A9472D] font-bold">({monumentsCount})</span>
                </button>
                <button
                  onClick={() => scrollToSection('about')}
                  className="p-2.5 text-left bg-[#F5F3ED] rounded-xl border border-[#E3DFD5] hover:bg-[#FFFEFA]"
                >
                  About
                </button>
              </div>

              <div className="pt-2 border-t border-[#E3DFD5] flex items-center justify-between text-xs font-mono">
                <Link
                  to="/history"
                  onClick={() => setMobileMenuOpen(false)}
                  className="inline-flex items-center gap-1.5 text-[#6E7069] hover:text-[#171816]"
                >
                  <History className="w-3.5 h-3.5 text-[#A9472D]" />
                  <span>Archival Log ({history.length})</span>
                </Link>

                {user ? (
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      logout();
                    }}
                    className="text-rose-700 font-semibold cursor-pointer"
                  >
                    Sign Out ({user.name})
                  </button>
                ) : (
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="text-[#A9472D] font-semibold"
                  >
                    Sign In
                  </Link>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}