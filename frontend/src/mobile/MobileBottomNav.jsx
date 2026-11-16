import React from 'react';
import { Compass, Landmark, Camera, BookOpen, Info } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export default function MobileBottomNav({ activeTab, onSelectTab }) {
  const { history } = useAuth();
  const scanCount = history?.length || 0;

  const NAV_ITEMS = [
    { id: 'discover', label: 'Discover', icon: Compass },
    { id: 'archive', label: 'Archive', icon: Landmark },
    { id: 'recognise', label: 'Recognise', icon: Camera, isCenter: true },
    { id: 'history', label: 'Log', icon: BookOpen, badge: scanCount > 0 ? scanCount : null },
    { id: 'about', label: 'About', icon: Info },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-[#F5F3ED]/95 backdrop-blur-lg border-t border-[#E3DFD5] shadow-lg mobile-safe-bottom">
      <div className="max-w-md mx-auto px-2 py-1.5 flex items-center justify-around">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          if (item.isCenter) {
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className="relative -top-4 flex flex-col items-center group cursor-pointer focus:outline-none"
              >
                <div
                  className={`w-13 h-13 rounded-full flex items-center justify-center shadow-lg transition-transform duration-200 active:scale-95 ${
                    isActive
                      ? 'bg-[#A9472D] text-white ring-4 ring-[#A9472D]/20'
                      : 'bg-[#171816] text-[#FFFEFA] hover:bg-[#A9472D]'
                  }`}
                >
                  <Icon className="w-6 h-6 stroke-[2.2]" />
                </div>
                <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-[#A9472D] mt-0.5">
                  Scan
                </span>
              </button>
            );
          }

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className="relative flex flex-col items-center justify-center py-1 px-3 text-[#6E7069] transition-colors focus:outline-none active:scale-95"
            >
              {isActive && (
                <motion.div
                  layoutId="activeTabIndicator"
                  className="absolute inset-0 bg-[#A9472D]/10 rounded-xl -z-10"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
              <div className="relative">
                <Icon
                  className={`w-5 h-5 transition-colors duration-150 ${
                    isActive ? 'text-[#A9472D] stroke-[2.4]' : 'text-[#6E7069]'
                  }`}
                />
                {item.badge !== null && item.badge !== undefined && (
                  <span className="absolute -top-1.5 -right-2 min-w-[15px] h-[15px] px-1 rounded-full bg-[#A9472D] text-white font-mono text-[9px] font-bold flex items-center justify-center">
                    {item.badge > 99 ? '99+' : item.badge}
                  </span>
                )}
              </div>
              <span
                className={`text-[10px] font-mono tracking-tight mt-1 transition-colors duration-150 ${
                  isActive ? 'text-[#171816] font-bold' : 'text-[#6E7069]'
                }`}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

