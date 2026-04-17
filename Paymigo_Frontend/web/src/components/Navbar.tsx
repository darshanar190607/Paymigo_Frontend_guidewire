import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Zap, Menu, X, LogOut, User as UserIcon } from 'lucide-react';
import { cn, isAdminUser } from '@/lib/utils';
import { useAuth } from '../App';
import { logout } from '../firebase';

const NAV_LINKS = [
  { name: 'How it Works', to: '/how-it-works' },
  { name: 'Plans',        to: '/plans' },
  { name: 'AI Models',   to: '/ai-models' },
  { name: 'Dashboard',   to: '/dashboard' },
];

const Navbar = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isAdmin = isAdminUser(user?.email);
  const links = isAdmin ? [...NAV_LINKS, { name: 'Admin', to: '/admin' }] : NAV_LINKS;

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
    setMobileMenuOpen(false);
  };

  return (
    <nav className={cn(
      'fixed top-0 w-full z-[100] transition-all duration-300 px-6 py-2 flex justify-between items-center',
      scrolled || mobileMenuOpen ? 'bg-white/80 backdrop-blur-md border-b border-border/50' : 'bg-transparent'
    )}>
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2">
        <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center shadow-lg shadow-accent/20 gradient-bg">
          <Shield className="text-white w-5 h-5" />
        </div>
        <span className="text-xl font-display font-black tracking-tighter text-text-primary">Paymigo</span>
      </Link>

      {/* Desktop Nav */}
      <div className="hidden md:flex items-center gap-8 text-sm font-bold text-text-secondary">
        {links.map((link) => (
          <Link
            key={link.name}
            to={link.to}
            className="hover:text-accent transition-colors uppercase tracking-widest text-[11px]"
          >
            {link.name}
          </Link>
        ))}

        {user ? (
          <div className="flex items-center gap-4">
            <Link to="/profile" className="flex items-center gap-2 hover:text-accent transition-colors">
              {user.photoURL ? (
                <img src={user.photoURL} alt={user.displayName || ''} className="w-8 h-8 rounded-full border border-accent/20" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
                  <UserIcon className="w-4 h-4 text-accent" />
                </div>
              )}
              <span className="text-[11px] uppercase tracking-widest">{user.displayName?.split(' ')[0]}</span>
            </Link>
            <button
              onClick={handleLogout}
              className="p-2 text-text-secondary hover:text-danger transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <Link
            to="/login"
            className="px-6 py-1.5 bg-accent text-white rounded-full font-bold hover:scale-105 transition-all shadow-lg shadow-accent/20 gradient-bg"
          >
            Sign In
          </Link>
        )}
      </div>

      {/* Mobile Menu Toggle */}
      <button
        className="md:hidden p-2 text-text-secondary"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
      >
        {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="absolute top-full left-0 w-full bg-white border-b border-border/50 p-6 flex flex-col gap-4 md:hidden animate-in fade-in slide-in-from-top-4 shadow-2xl">
          {links.map((link) => (
            <Link
              key={link.name}
              to={link.to}
              className="text-lg font-bold py-2 uppercase tracking-widest text-[12px] text-text-secondary"
              onClick={() => setMobileMenuOpen(false)}
            >
              {link.name}
            </Link>
          ))}
          {user ? (
            <>
              <Link to="/profile" className="text-left text-lg font-bold py-2 uppercase tracking-widest text-[12px] text-text-secondary" onClick={() => setMobileMenuOpen(false)}>
                Profile
              </Link>
              <button
                onClick={handleLogout}
                className="w-full py-4 bg-danger/10 text-danger rounded-xl font-bold mt-2"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              to="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full py-4 text-center bg-accent text-white rounded-xl font-bold mt-2 shadow-lg shadow-accent/20 gradient-bg"
            >
              Sign In
            </Link>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
