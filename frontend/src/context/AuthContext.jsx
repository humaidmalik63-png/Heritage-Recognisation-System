import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const DEFAULT_DEMO_USER = {
  id: 'usr_curator_01',
  name: 'Dr. Eleanor Vance',
  title: 'Senior Archaeologist & Curator',
  email: 'curator@heritage.org',
  role: 'Certified Curatorial Fellow',
  badgeNumber: 'ASI-FELLOW-2026-88',
  department: 'Division of Monument Epigraphy & AI Archival Systems',
};

// Default initial historic scans for demonstration
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
    thumbnail: 'http://localhost:8000/dataset/taj_mahal/img_1.jpg',
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
    thumbnail: 'http://localhost:8000/dataset/charminar/img_2.jpg',
    coordinates: { lat: 17.3616, lng: 78.4747 },
  },
];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session from localStorage on mount
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
          // Initialize demo scans for new sessions
          setHistory(INITIAL_DEMO_SCANS);
          localStorage.setItem(userHistoryKey, JSON.stringify(INITIAL_DEMO_SCANS));
        }
      } else {
        // Automatically seed demo user in storage
        const existingUsers = JSON.parse(localStorage.getItem('heritage_users') || '[]');
        if (!existingUsers.some((u) => u.email === DEFAULT_DEMO_USER.email)) {
          existingUsers.push({
            ...DEFAULT_DEMO_USER,
            password: 'curator123',
          });
          localStorage.setItem('heritage_users', JSON.stringify(existingUsers));
        }
      }
    } catch (e) {
      console.error('Failed to parse auth state:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const trimmedEmail = email.trim().toLowerCase();
    const storedUsers = JSON.parse(localStorage.getItem('heritage_users') || '[]');

    // Check against registered users or default demo
    let found = storedUsers.find(
      (u) => u.email.toLowerCase() === trimmedEmail && u.password === password
    );

    if (!found && trimmedEmail === DEFAULT_DEMO_USER.email && password === 'curator123') {
      found = { ...DEFAULT_DEMO_USER, password: 'curator123' };
    }

    if (!found) {
      throw new Error('Invalid curatorial credentials. Please check your email and password.');
    }

    const { password: _, ...userProfile } = found;
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

    const newUser = {
      id: `usr_${Date.now()}`,
      name: name.trim(),
      email: trimmedEmail,
      title: 'Junior Field Archaeologist',
      role: 'Curatorial Registry Associate',
      badgeNumber: `ASI-REG-${Math.floor(1000 + Math.random() * 9000)}`,
      department: 'Field Survey & Heritage Digital Register',
      password,
    };

    storedUsers.push(newUser);
    localStorage.setItem('heritage_users', JSON.stringify(storedUsers));

    const { password: _, ...userProfile } = newUser;
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
      thumbnail: thumbnailSrc || `http://localhost:8000/dataset/${scanResult.monument_key}/img_1.jpg`,
      coordinates: scanResult.coordinates,
      historical_summary: scanResult.historical_summary,
      structural_features_detected: scanResult.structural_features_detected || [],
      pipeline_telemetry: scanResult.pipeline_telemetry,
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

