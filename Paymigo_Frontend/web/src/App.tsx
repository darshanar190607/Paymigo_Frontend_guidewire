import React, { createContext, useContext, useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { onAuthStateChanged, User } from 'firebase/auth';
import { auth } from './firebase';
import Navbar from './components/Navbar';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Onboard from './pages/Onboard';
import Dashboard from './pages/Dashboard';
import Wallet from './pages/Wallet';
import Profile from './pages/Profile';
import Admin from './pages/Admin';
import Plans from './pages/Plans';
import PlanCheckout from './pages/PlanCheckout';
import HowItWorks from './pages/HowItWorks';
import AIModels from './pages/AIModels';
import WatchDemo from './pages/WatchDemo';
import Insurer from './pages/Insurer';

// ─── Auth Context ─────────────────────────────────────────────────────────────

interface AuthContextType {
  user: User | null;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  setLoading: () => {},
});

export const useAuth = () => useContext(AuthContext);

// ─── Protected Route ──────────────────────────────────────────────────────────

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!user) {
    // Preserve the attempted URL for redirect after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [user, setUser]       = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check localStorage for our backend user
    const token = localStorage.getItem('token');
    const storedUserStr = localStorage.getItem('paymigo_user');
    
    if (token && storedUserStr) {
      try {
        const parsedUser = JSON.parse(storedUserStr);
        // Ensure standard fields map correctly so other components don't break
        if (!parsedUser.displayName) parsedUser.displayName = parsedUser.name || parsedUser.email;
        if (!parsedUser.uid) parsedUser.uid = parsedUser.id;
        setUser(parsedUser);
      } catch (e) {
        localStorage.removeItem('token');
        localStorage.removeItem('paymigo_user');
      }
    } else {
      // Also check if logged in via firebase as fallback
      const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
        if (!localStorage.getItem('token')) {
          setUser(null); // Force null if no backend token exists
        }
        setLoading(false);
      });
      return () => unsubscribe();
    }
    
    setLoading(false);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, setLoading }}>
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="pt-20">
          <Routes>
            {/* Public routes */}
            <Route path="/"            element={<Landing />} />
            <Route path="/login"       element={<Login />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/plans"       element={<Plans />} />
            <Route path="/plans/:id"   element={<PlanCheckout />} />
            <Route path="/demo"        element={<WatchDemo />} />
            <Route path="/ai-models"   element={<AIModels />} />
            <Route path="/insurer"     element={<Insurer />} />

            {/* Protected routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/onboard"   element={<Onboard />} />
            <Route path="/wallet"    element={<ProtectedRoute><Wallet /></ProtectedRoute>} />
            <Route path="/profile"   element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            <Route path="/admin"     element={<ProtectedRoute><Admin /></ProtectedRoute>} />

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </AuthContext.Provider>
  );
}
