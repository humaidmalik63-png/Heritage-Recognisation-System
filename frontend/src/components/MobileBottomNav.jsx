import React from 'react';
import { motion } from 'framer-motion';
import { Compass, BookOpen, ScanLine, History, Landmark } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { buttonTapVariants } from '../utils/animations';

export default function MobileBottomNav({
  onRecognizeClick,
  onOpenCatalog,
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const { history } = useAuth();

  const isHome = location.pathname === '/';
  const isHistory = location.pathname === '/history';

  const scrollToSection = (id) => {
    if (!isHome) {
      navigate(`/#${id}`);
      setTimeout(() => {
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      return;
    }
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const navItems = [
    {
      id: 'discover',
      label: 'Discover',
      icon: Compass,
      onClick: () => scrollToSection('discover'),
      isActive: isHome,
    },
    {
      id: 'archive',
      label: 'Archive',
      icon: BookOpen,
      onClick: () => scrollToSection('archive'),
      isActive: false,
    },
    {
      id: 'recognise',
      label: 'Recognise',
      icon: ScanLine,
      isPrimary: true,
      onClick: () => {
        if (onRecognizeClick) {
          onRecognizeClick();
        } else {
          scrollToSection('recognition');
        }
      },
    },
    {
      id: 'history',
      label: 'Log',
      icon: History,
      badge: history.length,
      onClick: () => navigate('/history'),
      isActive: isHistory,
    },
    {
      id: 'about',
      label: 'About',
      icon: Landmark,
      onClick: () => scrollToSection('about'),
      isActive: false,
    },
  ];

  return (
    <nav
      aria-label="Mobile Navigation"
      className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-[#FFFEFA]/95 backdrop-blur-md border-t border-[#E3DFD5] shadow-[0_-4px_20px_rgba(23,24,22,0.06)] px-2 pt-1 pb-[max(env(safe-area-inset-bottom,8px),8px)]"
    >
      <div className="max-w-md mx-auto flex items-center justify-around">
        {navItems.map((item) => {
          const Icon = item.icon;

          if (item.isPrimary) {
            return (
              <motion.button
                key={item.id}
                whileTap={{ scale: 0.92 }}
                onClick={item.onClick}
                className="relative -top-3 flex flex-col items-center justify-center p-3 rounded-full bg-gradient-to-tr from-[#A9472D] via-[#B84E34] to-[#993E26] text-white shadow-[0_6px_20px_rgba(169,71,45,0.4)] border-2 border-[#FFFEFA] cursor-pointer"
                title="Recognise a Monument"
                aria-label="Recognise a Monument"
              >
                <Icon className="w-5 h-5 text-[#B99A5B]" />
                <span className="sr-only">Recognise</span>
              </motion.button>
            );
          }

          return (
            <motion.button
              key={item.id}
              whileTap={{ scale: 0.94 }}
              onClick={item.onClick}
              className={`flex flex-col items-center justify-center py-1.5 px-3 rounded-xl transition-colors min-w-[56px] relative cursor-pointer ${
                item.isActive
                  ? 'text-[#A9472D] font-semibold'
                  : 'text-[#6E7069] hover:text-[#171816]'
              }`}
            >
              <div className="relative">
                <Icon className="w-4 h-4 mb-0.5" />
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="absolute -top-1 -right-2.5 min-w-[14px] h-[14px] px-0.5 bg-[#A9472D] text-white text-[9px] font-mono font-bold rounded-full flex items-center justify-center leading-none">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className="text-[10px] font-sans tracking-tight">
                {item.label}
              </span>
              {item.isActive && (
                <span className="w-1 h-1 rounded-full bg-[#A9472D] mt-0.5" />
              )}
            </motion.button>
          );
        })}
      </div>
    </nav>
  );
}

