import React from 'react';
import { motion } from 'motion/react';
import { 
  Shield, 
  Zap, 
  CheckCircle2, 
  ArrowRight, 
  Database,
  Cpu,
  Smartphone,
  Lock,
  Globe,
  BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';

const HowItWorks = () => {
  const steps = [
    {
      title: "Data Ingestion",
      desc: "We ingest real-time weather data from IMD, Skymet, and our own IoT rain gauges at a 500m grid level.",
      icon: Database,
      color: "text-accent",
      bg: "bg-accent/10"
    },
    {
      title: "AI Risk Assessment",
      desc: "Our XGBoost models analyze the disruption potential based on rainfall intensity, wind speed, and historical zone data.",
      icon: Cpu,
      color: "text-warning",
      bg: "bg-warning/10"
    },
    {
      title: "Parametric Trigger",
      desc: "If the data crosses the predefined threshold (e.g., 15mm/hr), a trigger is automatically generated.",
      icon: Zap,
      color: "text-success",
      bg: "bg-success/10"
    },
    {
      title: "Instant Payout",
      desc: "Payouts are pushed instantly to your linked UPI ID. No claims filing required.",
      icon: Smartphone,
      color: "text-accent",
      bg: "bg-accent/10"
    }
  ];

  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Hero Section */}
      <header className="relative py-20 px-6 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full hero-glow -z-10 opacity-50" />
        
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl md:text-6xl font-display font-black leading-tight mb-8 tracking-tight">
              The Science of <br />
              <span className="text-accent">Automatic Protection</span>
            </h1>
            <p className="text-lg text-text-secondary mb-12 max-w-2xl mx-auto leading-relaxed">
              Traditional insurance is broken. It's slow, manual, and full of fine print. 
              Paymigo uses <strong>Parametric Triggers</strong> to automate everything.
            </p>
            <a 
              href="/onboard" 
              className="inline-flex items-center gap-2 px-8 py-4 bg-accent text-background rounded-xl font-bold hover:scale-105 transition-transform"
            >
              Get Started Now <ArrowRight className="w-5 h-5" />
            </a>
          </motion.div>
        </div>
      </header>

      {/* Process Steps */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="glass-card p-8 relative"
              >
                <div className="absolute -top-4 -left-4 w-10 h-10 bg-background border border-white/10 rounded-full flex items-center justify-center font-bold text-accent text-xs">
                  0{i + 1}
                </div>
                <div className={cn("w-14 h-14 rounded-2xl flex items-center justify-center mb-6", step.bg, step.color)}>
                  <step.icon className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-bold mb-4">{step.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="py-24 px-6 bg-surface/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-display font-bold mb-6">Old Way vs. Paymigo</h2>
            <p className="text-text-secondary">Why parametric insurance is the future of the gig economy.</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="glass-card p-8 border-danger/10 opacity-60">
              <h3 className="text-xl font-bold mb-8 flex items-center gap-2 text-danger">
                <XCircle className="w-6 h-6" /> Traditional Insurance
              </h3>
              <ul className="space-y-6">
                {[
                  "Manual claim filing required",
                  "Proof of loss (photos, bills) needed",
                  "30-45 days for claim settlement",
                  "High rejection rates due to fine print",
                  "Complex paperwork and agent calls"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-4 text-text-secondary">
                    <div className="w-1.5 h-1.5 rounded-full bg-danger" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="glass-card p-8 border-accent/40 bg-accent/5">
              <h3 className="text-xl font-bold mb-8 flex items-center gap-2 text-accent">
                <CheckCircle2 className="w-6 h-6" /> Paymigo Parametric
              </h3>
              <ul className="space-y-6">
                {[
                  "Zero-touch automatic triggers",
                  "No proof of loss required",
                  "90-second instant UPI payouts",
                  "100% transparent data-driven rules",
                  "Fully digital, AI-managed experience"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-4 text-text-primary font-medium">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="order-2 md:order-1">
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Data Sources", val: "12+", icon: Globe },
                { label: "Grid Precision", val: "500m", icon: BarChart3 },
                { label: "AI Models", val: "XGBoost", icon: Cpu },
                { label: "Security", val: "AES-256", icon: Lock },
              ].map((item, i) => (
                <div key={i} className="glass-card p-6 text-center">
                  <item.icon className="w-6 h-6 text-accent mx-auto mb-3" />
                  <div className="text-xl font-mono font-bold">{item.val}</div>
                  <div className="text-[10px] text-text-secondary uppercase font-bold tracking-widest">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="order-1 md:order-2">
            <h2 className="text-3xl md:text-5xl font-display font-bold mb-8 leading-tight">
              Powered by <br />
              <span className="text-accent">Hyperlocal Data</span>
            </h2>
            <p className="text-text-secondary leading-relaxed mb-8">
              We don't just look at city-wide weather. We monitor rainfall at the micro-zone level. 
              If it rains in T. Nagar but not in Adyar, only the partners in T. Nagar get paid. 
              This precision allows us to offer lower premiums and higher payouts.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <Shield className="text-accent w-6 h-6" />
            <span className="text-xl font-display font-bold">Paymigo</span>
          </div>
          <p className="text-text-secondary text-sm">
            Built for DEVTrails 2026 • India's first parametric gig insurance
          </p>
          <div className="flex gap-6">
            <a href="/how-it-works" className="text-sm text-text-secondary hover:text-accent transition-colors">Privacy</a>
            <a href="/how-it-works" className="text-sm text-text-secondary hover:text-accent transition-colors">Terms</a>
            <a href="/how-it-works" className="text-sm text-text-secondary hover:text-accent transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

const XCircle = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
  </svg>
);

export default HowItWorks;
