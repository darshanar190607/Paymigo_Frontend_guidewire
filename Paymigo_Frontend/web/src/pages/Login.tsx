import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import { Shield, LogIn, User, Lock, Mail, UserPlus } from 'lucide-react';
import { signInWithGoogle, auth, db } from '../firebase';
import { signInWithCustomToken, getAuth } from 'firebase/auth';
import { doc, getDoc } from 'firebase/firestore';
import { useAuth } from '../App';
import { cn, isAdminUser } from '@/lib/utils';

const Login = () => {
  const { user, loading: authLoading, setLoading } = useAuth();
  const navigate = useNavigate();
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<'worker' | 'admin'>('worker');
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    const checkRedirect = async () => {
      if (!authLoading && user && user.uid) {
        if (window.location.pathname === '/login') {
          let target = '/dashboard';
          if (isAdminUser(user.email)) {
            target = '/admin';
          } else {
            try {
              const workerDoc = await getDoc(doc(db, 'workers', user.uid));
              if (!workerDoc.exists()) {
                target = '/onboard';
              }
            } catch(e) {}
          }
          navigate(target, { replace: true });
        }
      }
    };
    checkRedirect();
  }, [user, authLoading]);

  const handleGoogleLogin = async () => {
    if (isLoggingIn) return;
    setIsLoggingIn(true);
    setError(null);
    setLoading(true);
    try {
      const result = await signInWithGoogle();
      const idToken = await result.user.getIdToken();
      
      const response = await fetch('http://localhost:3000/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken })
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Google login failed on backend");
      }
      
      console.log("Applying custom token:", data.firebaseToken);
      console.log("Applying custom token:", data.firebaseToken);
      await signInWithCustomToken(auth, data.firebaseToken);
      console.log("Firebase custom token successfully applied.");

      localStorage.setItem('token', data.token);
      localStorage.setItem('paymigo_user', JSON.stringify(data.worker));
      
      if (data.worker.pincode === '000000' || data.worker.phone.startsWith('PENDING_')) {
          navigate('/onboard', { replace: true });
          return;
      }

      let target = '/dashboard';
      if (isAdminUser(data.worker.email)) {
        target = '/admin';
      }
      navigate(target, { replace: true });
      
    } catch (err: any) {
      console.error("Login failed:", err);
      setError(err.message || "Login failed");
      setIsLoggingIn(false);
      setLoading(false);
    }
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoggingIn) return;

    if (!email || !password) {
      setError('Please enter your email and password.');
      return;
    }

    setIsLoggingIn(true);
    setError(null);
    setLoading(true);
    try {
      if (mode === 'signup') {
        const response = await fetch('http://localhost:3000/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            email, 
            password, 
            phone: 'PENDING_' + Math.random().toString(36).substring(7), // Mock phone, real one handled in Onboarding
            pincode: '000000', // Mock pincode, handled later
            zoneId: 'default' 
          })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        console.log("Applying custom token (register):", data.firebaseToken);
        console.log("Applying custom token (register):", data.firebaseToken);
        await signInWithCustomToken(auth, data.firebaseToken);
        console.log("Firebase custom token successfully applied.");

        localStorage.setItem('token', data.token);
        localStorage.setItem('paymigo_user', JSON.stringify(data.worker));
        navigate('/onboard', { replace: true });

      } else {
        const response = await fetch('http://localhost:3000/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        console.log("Applying custom token (login):", data.firebaseToken);
        console.log("Applying custom token (login):", data.firebaseToken);
        await signInWithCustomToken(auth, data.firebaseToken);
        console.log("Firebase custom token successfully applied.");

        localStorage.setItem('token', data.token);
        localStorage.setItem('paymigo_user', JSON.stringify(data.worker));
        
        // Simple logic to check if they need onboarding
        if (data.worker.pincode === '000000' || data.worker.phone.startsWith('PENDING_')) {
            navigate('/onboard', { replace: true });
            return;
        }

        let target = '/dashboard';
        if (isAdminUser(data.worker.email)) {
          target = '/admin';
        }
        navigate(target, { replace: true });
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
      setIsLoggingIn(false);
      setLoading(false);
    }
  };

  if (authLoading || (user && !authLoading)) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-6 py-20">
      <div className="absolute inset-0 hero-glow opacity-30 z-0" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative z-10 glass-card p-8 md:p-12 max-w-lg w-full border-accent/20"
      >
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-accent rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-accent/20 gradient-bg">
            <Shield className="text-white w-8 h-8" />
          </div>
          <h1 className="text-3xl font-display font-black mb-2 tracking-tight">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h1>
          <p className="text-text-secondary text-sm font-medium">
            {role === 'worker' ? 'Gig Worker Portal' : 'Administrator Portal'}
          </p>
        </div>

        {/* Role Selector */}
        <div className="flex p-1 bg-surface rounded-2xl mb-8">
          <button 
            onClick={() => setRole('worker')}
            className={cn(
              "flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2",
              role === 'worker' ? "bg-white text-accent shadow-sm" : "text-text-secondary hover:text-text-primary"
            )}
          >
            <User className="w-4 h-4" />
            Worker
          </button>
          <button 
            onClick={() => setRole('admin')}
            className={cn(
              "flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2",
              role === 'admin' ? "bg-white text-accent shadow-sm" : "text-text-secondary hover:text-text-primary"
            )}
          >
            <Shield className="w-4 h-4" />
            Admin
          </button>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={role}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {error && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-xl text-danger text-xs font-bold"
              >
                {error}
              </motion.div>
            )}

            <form onSubmit={handleEmailAuth} className="space-y-4 mb-8">
              <div className="space-y-2">
                <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest ml-1">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                  <input 
                    type="email" 
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-surface border border-border rounded-2xl outline-none focus:border-accent transition-all text-sm"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest ml-1">Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                  <input 
                    type="password" 
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-surface border border-border rounded-2xl outline-none focus:border-accent transition-all text-sm"
                    required
                  />
                </div>
              </div>

              <button 
                type="submit"
                disabled={isLoggingIn}
                className="w-full py-4 bg-accent text-white rounded-2xl font-bold text-sm flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-accent/20 gradient-bg disabled:opacity-50"
              >
                {isLoggingIn ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    {mode === 'login' ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
                    {mode === 'login' ? 'Sign In' : 'Create Account'}
                  </>
                )}
              </button>
            </form>

            <div className="relative mb-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border/50"></div>
              </div>
              <div className="relative flex justify-center text-[10px] uppercase tracking-widest font-black">
                <span className="px-4 bg-white text-text-secondary">Or continue with</span>
              </div>
            </div>

            <button 
              onClick={handleGoogleLogin}
              disabled={isLoggingIn}
              className="w-full py-4 bg-white border border-border rounded-2xl font-bold text-sm flex items-center justify-center gap-3 hover:bg-surface transition-all shadow-sm disabled:opacity-50"
            >
              <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5" />
              Google Account
            </button>

            <div className="mt-8 text-center">
              <button 
                onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
                className="text-xs font-bold text-text-secondary hover:text-accent transition-colors"
              >
                {mode === 'login' ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
        
        <div className="mt-10 pt-8 border-t border-border/50 text-center">
          <p className="text-[10px] text-text-secondary font-black uppercase tracking-widest">
            India's first parametric gig insurance
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
