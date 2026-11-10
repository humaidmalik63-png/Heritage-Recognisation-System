import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

// Initial archival demo scans for user history visualization
const INITIAL_DEMO_SCANS = [
  {
    id: 'scan_init_01',
    timestamp: '2026-11-04T18:42:00.000Z',
    monument_name: 'Taj Mahal',
    monument_key: 'taj_mahal',
    catalog_id: 'ASI-ARCH-TAJ-01',
    verification_tier: 'TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX',
    confidence_score: 99.8,
    location: 'Agra, Uttar Pradesh',
    architectural_style: 'Mughal Architecture',
    built_by_or_era: 'Mughal Emperor Shah Jahan (c. 1631–1653)',
    thumbnail: '/assets/heritage/taj-mahal.jpg',
    coordinates: { lat: 27.1751, lng: 78.0421 },
  },
  {
    id: 'scan_init_02',
    timestamp: '2026-11-04T15:15:00.000Z',
    monument_name: 'Charminar',
    monument_key: 'charminar',
    catalog_id: 'ASI-ARCH-CHA-06',
    verification_tier: 'TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX',
    confidence_score: 99.8,
    location: 'Hyderabad, Telangana',
    architectural_style: 'Indo-Islamic (Qutb Shahi) Architecture',
    built_by_or_era: 'Muhammad Quli Qutb Shah (c. 1591)',
    thumbnail: '/assets/heritage/qutub-minar.jpg',
    coordinates: { lat: 17.3616, lng: 78.4747 },
  },
];

/**
 * Hash password client-side using Web Crypto API SHA-256
 * (prevents plaintext storage in localStorage)
 */
async function hashPassword(plainText) {
  const enc = new TextEncoder().encode(plainText);
  const buf = await window.crypto.subtle.digest('SHA-256', enc);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session from localStorage on mount (no auto-login, no default credentials)
  useEffect(() => {
    try {
      const storedUser = localStorage.getItem('heritage_current_user');
      if (storedUser) {
        const parsed = JSON.parse(storedUser);
        setUser(parsed);
        const userHistoryKey = `heritage_history_${parsed.email}`;
        const storedHistory = localStorage.getItem(userHistoryKey);
        if (storedHistory) {
          setHistory(JSON.parse(storedHistory));
        } else {
          setHistory(INITIAL_DEMO_SCANS);
        }
      } else {
        // Guest mode: unauthenticated by default
        setUser(null);
        setHistory([]);
      }
    } catch (e) {
      console.error('Failed to parse auth state:', e);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const trimmedEmail = email.trim().toLowerCase();
    const storedUsers = JSON.parse(localStorage.getItem('heritage_users') || '[]');
    const passwordHash = await hashPassword(password);

    // Verify against registered local users with secure hash comparison
    const found = storedUsers.find(
      (u) => u.email.toLowerCase() === trimmedEmail && u.passwordHash === passwordHash
    );

    if (!found) {
      throw new Error('Invalid curatorial credentials. Please check your email and password.');
    }

    const { passwordHash: _, ...userProfile } = found;
    setUser(userProfile);
    localStorage.setItem('heritage_current_user', JSON.stringify(userProfile));

    // Load user's personal history
    const userHistoryKey = `heritage_history_${userProfile.email}`;
    const storedHistory = localStorage.getItem(userHistoryKey);
    if (storedHistory) {
      setHistory(JSON.parse(storedHistory));
    } else {
      setHistory(INITIAL_DEMO_SCANS);
      localStorage.setItem(userHistoryKey, JSON.stringify(INITIAL_DEMO_SCANS));
    }

    return userProfile;
  };

  const signup = async (name, email, password) => {
    const trimmedEmail = email.trim().toLowerCase();
    const storedUsers = JSON.parse(localStorage.getItem('heritage_users') || '[]');

    if (storedUsers.some((u) => u.email.toLowerCase() === trimmedEmail)) {
      throw new Error('An archival account with this official email address already exists.');
    }

    const passwordHash = await hashPassword(password);

    const newUser = {
      id: `usr_${Date.now()}`,
      name: name.trim(),
      email: trimmedEmail,
      title: 'Field Research Associate',
      role: 'Curatorial Registry Associate',
      badgeNumber: `ASI-REG-${Math.floor(1000 + Math.random() * 9000)}`,
      department: 'Field Survey & Heritage Digital Register',
      passwordHash,
    };

    storedUsers.push(newUser);
    localStorage.setItem('heritage_users', JSON.stringify(storedUsers));

    const { passwordHash: _, ...userProfile } = newUser;
    setUser(userProfile);
    localStorage.setItem('heritage_current_user', JSON.stringify(userProfile));

    // Initialize with demo scans
    setHistory(INITIAL_DEMO_SCANS);
    localStorage.setItem(`heritage_history_${userProfile.email}`, JSON.stringify(INITIAL_DEMO_SCANS));

    return userProfile;
  };

  const logout = () => {
    setUser(null);
    setHistory([]);
    localStorage.removeItem('heritage_current_user');
  };

  const addScanToHistory = (scanResult, thumbnailSrc) => {
    if (!user) return;

    const newScanEntry = {
      id: `scan_${Date.now()}`,
      timestamp: new Date().toISOString(),
      monument_name: scanResult.monument_name || 'Unidentified Heritage Landmark',
      monument_key: scanResult.monument_key,
      catalog_id: scanResult.catalog_id || 'ASI-ARCH-NEW-00',
      verification_tier: scanResult.verification_tier,
      confidence_score: scanResult.confidence_score,
      location: scanResult.location || 'Location Recorded',
      architectural_style: scanResult.architectural_style || 'Historic Heritage',
      built_by_or_era: scanResult.built_by_or_era || 'Historical Era',
      thumbnail: thumbnailSrc || '/assets/heritage/taj-mahal.jpg',
      coordinates: scanResult.coordinates,
      historical_summary: scanResult.historical_summary,
      structural_features_detected: scanResult.structural_features_detected || [],
      pipeline_telemetry: scanResult.pipeline_telemetry,
      uncertainty: scanResult.uncertainty,
      grounded_citations: scanResult.grounded_citations,
      preservation_status: scanResult.preservation_status,
    };

    setHistory((prev) => {
      const updated = [newScanEntry, ...prev.filter((item) => item.id !== newScanEntry.id)];
      const userHistoryKey = `heritage_history_${user.email}`;
      try {
        localStorage.setItem(userHistoryKey, JSON.stringify(updated.slice(0, 50)));
      } catch (err) {
        console.warn('Storage quota alert, saving without heavy thumbnails:', err);
      }
      return updated;
    });
  };

  const clearHistory = () => {
    if (!user) return;
    setHistory([]);
    localStorage.removeItem(`heritage_history_${user.email}`);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        history,
        isLoading,
        login,
        signup,
        logout,
        addScanToHistory,
        clearHistory,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

