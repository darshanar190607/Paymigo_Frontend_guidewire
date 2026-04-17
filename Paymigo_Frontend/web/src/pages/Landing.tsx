import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Shield, ArrowRight, CheckCircle2, ShieldCheck, Wallet, AlertCircle, Play, Sparkles, Zap, TrendingUp, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

const Landing = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background overflow-x-hidden selection:bg-accent selection:text-white">
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center px-6 pt-20 overflow-hidden noise-bg mesh-gradient">
        <div className="absolute inset-0 hero-glow z-0 opacity-40" />
        
        <div className="relative z-10 max-w-7xl mx-auto w-full">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left Side: Content */}
            <div className="text-left">
              <motion.div 
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, type: 'spring' }}
                className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-white border border-accent/20 text-accent text-[11px] font-black mb-8 uppercase tracking-[0.25em] shadow-[0_8px_30px_rgb(255,85,0,0.12)]"
              >
                <div className="w-2 h-2 rounded-full bg-accent animate-ping absolute" />
                <div className="w-2 h-2 rounded-full bg-accent relative z-10" />
                Live: Zone 4 Protection Active
              </motion.div>
              
              <motion.h1 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.1, ease: 'easeOut' }}
                className="text-5xl md:text-6xl lg:text-[5rem] font-display font-black leading-[1.05] mb-8 tracking-tight text-text-primary"
              >
                When the sky <span className="gradient-text inline-block hover:scale-[1.02] transition-transform cursor-default">shuts you down</span> <br />
                Paymigo pays <span className="relative inline-block">
                  <span className="italic font-serif font-light text-accent">instantly.</span>
                  <motion.svg className="absolute -bottom-2 left-0 w-full h-3 text-accent/30" viewBox="0 0 100 20" preserveAspectRatio="none" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1, delay: 0.8 }}><path d="M0 10 Q50 20 100 10" fill="transparent" stroke="currentColor" strokeWidth="4" strokeLinecap="round"/></motion.svg>
                </span>
              </motion.h1>

              <motion.p 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="text-lg md:text-xl text-text-secondary mb-12 max-w-lg leading-relaxed font-medium"
              >
                The world's first parametric income protection for 5M+ delivery partners. 
                Zero forms, zero waiting. Triggered by data, paid in 90 seconds.
              </motion.p>

              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5 }}
                className="flex flex-col sm:flex-row gap-5 items-start"
              >
                <a 
                  href="/onboard" 
                  className="px-8 py-5 bg-accent text-white rounded-2xl font-black text-base flex items-center justify-center gap-3 hover:glow-accent transition-all group shadow-2xl shadow-accent/30 gradient-bg border border-white/20 hover:scale-[1.02]"
                >
                  Shield Your Income <ArrowRight className="w-5 h-5 group-hover:translate-x-1.5 transition-transform" />
                </a>
                <a 
                  href="/demo" 
                  className="px-8 py-5 bg-white backdrop-blur-xl border border-border/80 rounded-2xl font-bold text-base hover:shadow-lg transition-all flex items-center gap-3 group"
                >
                  <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Play className="w-4 h-4 fill-accent text-accent" />
                  </div>
                  Watch AI Demo
                </a>
              </motion.div>
            </div>

            {/* Right Side: Spectacular Composition */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, x: 20 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              transition={{ duration: 1, delay: 0.4 }}
              className="relative hidden lg:block"
            >
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-gradient-to-tr from-accent/20 to-accent-secondary/10 blur-[100px] rounded-full animate-pulse-slow" />
              
              <div className="relative w-full h-[550px]">
                {/* Main Image Base */}
                <div className="absolute right-0 top-10 w-4/5 h-[450px] rounded-[2.5rem] overflow-hidden border-[8px] border-white shadow-2xl shadow-accent/10 transform rotate-2 hover:rotate-0 transition-transform duration-700">
                  <img 
                    src="https://images.unsplash.com/photo-1617347454431-f49d7ff5c3b1?auto=format&fit=crop&q=80&w=1000" 
                    alt="Delivery Partner" 
                    className="w-full h-full object-cover scale-105 hover:scale-100 transition-transform duration-1000"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                </div>

                {/* Floating Glass Metric 1: System Status */}
                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 1.2, type: 'spring' }}
                  className="absolute top-0 right-10 glass-card p-4 flex items-center gap-4 animate-float hover:scale-105 transition-transform cursor-default"
                >
                  <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center border border-accent/20">
                    <Sparkles className="w-6 h-6 text-accent" />
                  </div>
                  <div>
                    <div className="text-[10px] font-black text-text-secondary uppercase tracking-widest mb-1">AI Logic Engine</div>
                    <div className="text-sm font-bold flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span> Analyzing Grid
                    </div>
                  </div>
                </motion.div>

                {/* Floating Glass Metric 2: Payout */}
                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.9, type: 'spring' }}
                  className="absolute bottom-10 left-0 glass-card p-5 lg:p-6 w-72 animate-float hover:scale-105 transition-transform cursor-default z-20"
                  style={{ animationDelay: '1.5s' }}
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-full bg-success/10 flex items-center justify-center shrink-0 border border-success/20">
                      <Zap className="w-6 h-6 text-success" />
                    </div>
                    <div>
                      <div className="text-[10px] font-black text-text-secondary uppercase tracking-widest leading-none mb-1.5">Rainfall &gt; 15mm Detected</div>
                      <div className="text-sm font-bold text-success leading-none">Instant Payout Fired</div>
                    </div>
                  </div>
                  <div className="px-4 py-3 bg-surface rounded-xl border border-border/50">
                    <div className="text-[10px] uppercase text-text-secondary tracking-widest mb-1 font-bold">Smart Contract Execution</div>
                    <div className="text-2xl font-mono font-black text-text-primary">₹1,500.00</div>
                  </div>
                </motion.div>
                
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Problem Section - Brutalist Bento Style */}
      <section className="py-32 px-6 bg-surface relative overflow-hidden noise-bg">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-5 pr-8">
              <h2 className="text-5xl md:text-6xl font-display font-black mb-8 leading-tight">
                Rain shouldn't mean <br />
                <span className="gradient-text">Zero Earnings.</span>
              </h2>
              <p className="text-xl text-text-secondary mb-10 leading-relaxed font-medium">
                A single monsoon week can wipe out 40% of a delivery partner's monthly income. 
                Traditional insurance is too slow. Paymigo is parametric—meaning we pay based on 
                real-time weather data, not damage claims.
              </p>
              <div className="space-y-6">
                {[
                  { title: "Real-time Weather Monitoring", desc: "Hyper-local data from 1,200+ micro-zones." },
                  { title: "Zero Paperwork", desc: "No claim forms. No phone calls. No waiting." },
                  { title: "Instant Wallet Credit", desc: "Money hits your Paymigo wallet in 90 seconds." }
                ].map((item, i) => (
                  <div key={i} className="flex gap-5 items-start group cursor-default">
                    <div className="w-8 h-8 rounded-full bg-white border border-border shadow-sm flex items-center justify-center shrink-0 mt-0.5 group-hover:scale-110 group-hover:bg-accent/10 transition-all">
                      <CheckCircle2 className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <h4 className="font-bold text-lg mb-1">{item.title}</h4>
                      <p className="text-text-secondary text-sm">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-7 relative h-full">
              <div className="absolute -inset-10 bg-gradient-to-tr from-accent to-accent-secondary opacity-15 blur-[80px] rounded-full" />
              <div className="relative bento-card p-10 rotate-1 hover:rotate-0 transition-transform duration-700 bg-white/80 backdrop-blur-2xl border-white/60 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)]">
                <div className="flex justify-between items-center mb-10 border-b border-border pb-6">
                  <div className="text-sm font-black text-text-secondary uppercase tracking-[0.2em]">Weekly Loss Tracker</div>
                  <div className="px-4 py-1.5 bg-danger/10 text-danger text-[11px] font-black rounded-full uppercase flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-danger animate-pulse" /> Alert: Heavy Rain
                  </div>
                </div>
                <div className="space-y-5">
                  {[
                    { day: 'Mon', loss: 0, status: 'Clear' },
                    { day: 'Tue', loss: 450, status: 'Rain' },
                    { day: 'Wed', loss: 800, status: 'Storm' },
                    { day: 'Thu', loss: 600, status: 'Rain' },
                    { day: 'Fri', loss: 0, status: 'Clear' },
                  ].map((d, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-surface rounded-2xl border border-white hover:border-accent/30 transition-colors group">
                      <span className="font-black w-10 text-text-secondary group-hover:text-primary transition-colors">{d.day}</span>
                      <div className="flex-grow mx-6 h-3 bg-white border border-border/50 rounded-full overflow-hidden shadow-inner">
                        <motion.div 
                          initial={{ width: 0 }}
                          whileInView={{ width: `${(d.loss / 800) * 100}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 1, delay: i * 0.1, type: "spring" }}
                          className="h-full gradient-bg relative overflow-hidden"
                        >
                          <div className="absolute inset-0 bg-white/20 w-1/2 -skew-x-12 translate-x-[-150%] animate-[slide_3s_infinite]" />
                        </motion.div>
                      </div>
                      <span className={cn("font-mono font-black text-lg w-20 text-right", d.loss > 0 ? "text-danger" : "text-success")}>
                        {d.loss > 0 ? `-₹${d.loss}` : 'Clear'}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="mt-10 p-8 bg-text-primary rounded-3xl text-white text-center relative overflow-hidden shadow-2xl">
                  <div className="absolute inset-0 mesh-gradient opacity-20 mix-blend-screen" />
                  <div className="relative z-10">
                    <div className="text-sm font-bold uppercase tracking-[0.25em] opacity-80 mb-2 text-accent">Total Loss Avoided</div>
                    <div className="text-5xl font-display font-black">₹1,850</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid - Bento Layout */}
      <section className="py-32 px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-5xl font-display font-black mb-6">Engineered for the <span className="gradient-text">Gig Economy</span></h2>
            <p className="text-text-secondary max-w-2xl mx-auto text-xl font-medium tracking-wide">We've rebuilt insurance from the ground up. Fast, algorithmic, and undeniably transparent.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6 auto-rows-[250px]">
            {/* Bento Card 1 - Span 2 */}
            <div className="bento-card md:col-span-2 p-10 group bg-surface">
              <div className="absolute top-0 right-0 w-64 h-64 bg-accent/5 rounded-bl-full transition-transform group-hover:scale-110" />
              <div className="relative z-10 h-full flex flex-col justify-between">
                <div className="w-14 h-14 bg-white shadow-md rounded-2xl flex items-center justify-center mb-8 border border-border group-hover:border-accent/50 transition-colors">
                  <ShieldCheck className="w-7 h-7 text-accent" />
                </div>
                <div>
                  <h3 className="text-3xl font-black mb-3">Parametric Trust</h3>
                  <p className="text-text-secondary text-lg max-w-md">Payouts are completely governed by data APIs (Rainfall &gt; 5mm/hr), entirely skipping the subjective claims process.</p>
                </div>
              </div>
            </div>

            {/* Bento Card 2 */}
            <div className="bento-card p-10 group mesh-gradient">
              <div className="relative z-10 h-full flex flex-col justify-between">
                <div className="w-14 h-14 bg-white/50 backdrop-blur shadow-sm rounded-2xl flex items-center justify-center mb-8 border border-white">
                  <Zap className="w-7 h-7 text-accent" />
                </div>
                <div>
                  <h3 className="text-2xl font-black mb-3">90s Payouts</h3>
                  <p className="text-text-secondary font-medium text-sm">Smart contracts fire automatically. Cash hits the wallet within seconds of data validation.</p>
                </div>
              </div>
            </div>

            {/* Bento Card 3 */}
            <div className="bento-card bg-text-primary text-white p-10 group">
              <div className="absolute inset-0 bg-gradient-to-br from-text-primary to-black opacity-50" />
              <div className="relative z-10 h-full flex flex-col justify-between">
                <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mb-8 border border-white/20">
                  <TrendingUp className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-black mb-3 text-white">AI Risk Engine</h3>
                  <p className="text-white/60 font-medium text-sm">Our 6-layer machine learning stack predicts disruptions across micro-zones at 94% accuracy.</p>
                </div>
              </div>
            </div>

            {/* Bento Card 4 - Span 2 */}
            <div className="bento-card md:col-span-2 p-10 group border-accent/20 bg-gradient-to-tr from-surface to-white">
              <div className="relative z-10 h-full flex flex-col sm:flex-row gap-8 items-center">
                <div className="flex-1">
                  <div className="w-14 h-14 bg-accent/5 rounded-2xl flex items-center justify-center mb-8 border border-accent/10">
                    <Wallet className="w-7 h-7 text-accent" />
                  </div>
                  <h3 className="text-3xl font-black mb-3">Micro-Premiums</h3>
                  <p className="text-text-secondary text-lg">Coverage starting at just ₹69/week. Flexible wallet deductions natively integrated with your API. No multi-month lock-ins. Top up or pause instantly.</p>
                </div>
                <div className="w-48 h-48 rounded-full border-[10px] border-surface shadow-2xl flex items-center justify-center bg-white shrink-0 relative">
                  <div className="absolute inset-0 rounded-full border-4 border-accent/30 border-t-accent animate-spin" style={{ animationDuration: '3s' }} />
                  <span className="text-4xl font-black gradient-text">₹69</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-32 px-6 bg-text-primary text-white stats-section relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent blur-[120px] rounded-full" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-secondary blur-[120px] rounded-full" />
        </div>
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid md:grid-cols-4 gap-16 text-center">
            {[
              { val: "5M+", label: "Target Partners" },
              { val: "₹12Cr+", label: "Claims Capacity" },
              { val: "99.9%", label: "AI Accuracy" },
              { val: "1.2k", label: "Micro-Zones" }
            ].map((stat, i) => (
              <div key={i} className="stat-item">
                <div className="text-6xl md:text-7xl font-display font-black mb-4 gradient-text">{stat.val}</div>
                <div className="text-sm font-bold uppercase tracking-[0.2em] opacity-60">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6 relative overflow-hidden">
        <div className="max-w-5xl mx-auto glass-card p-16 md:p-24 text-center relative overflow-hidden border-accent/30">
          <div className="absolute -top-24 -right-24 w-64 h-64 bg-accent/10 blur-3xl rounded-full" />
          <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-accent-secondary/10 blur-3xl rounded-full" />
          
          <h2 className="text-4xl md:text-6xl font-display font-black mb-8 leading-tight">
            Ready to <span className="gradient-text">Shield Your Income?</span>
          </h2>
          <p className="text-xl text-text-secondary mb-12 max-w-2xl mx-auto">
            Join thousands of delivery partners who no longer fear the monsoon. 
            Get your first week of GigKavach for just ₹1.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <a href="/onboard" className="px-12 py-5 bg-accent text-white rounded-2xl font-bold text-xl hover:glow-accent transition-all shadow-2xl shadow-accent/20 gradient-bg">
              Start Your Protection
            </a>
            <a href="/plans" className="px-12 py-5 bg-surface border border-border rounded-2xl font-bold text-xl hover:bg-white transition-all">
              View All Plans
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 px-6 border-t border-border bg-surface/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center">
                  <Shield className="text-white w-6 h-6" />
                </div>
                <span className="text-3xl font-display font-black tracking-tighter">Paymigo</span>
              </div>
              <p className="text-text-secondary max-w-sm mb-8">
                India's first AI-powered parametric income insurance platform for food delivery partners. 
                Protecting the backbone of the digital economy.
              </p>
              <div className="flex gap-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="w-10 h-10 rounded-full bg-background border border-border flex items-center justify-center hover:border-accent transition-colors cursor-pointer">
                    <div className="w-4 h-4 bg-text-secondary rounded-sm" />
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="font-bold mb-6 uppercase tracking-widest text-xs">Platform</h4>
              <ul className="space-y-4 text-text-secondary">
                <li><a href="/how-it-works" className="hover:text-accent transition-colors">How it Works</a></li>
                <li><a href="/plans" className="hover:text-accent transition-colors">Pricing Plans</a></li>
                <li><a href="/ai-models" className="hover:text-accent transition-colors">AI & ML Stack</a></li>
                <li><a href="/insurer" className="hover:text-accent transition-colors">For Insurers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-6 uppercase tracking-widest text-xs">Company</h4>
              <ul className="space-y-4 text-text-secondary">
                <li><a href="#" className="hover:text-accent transition-colors">About Us</a></li>
                <li><a href="#" className="hover:text-accent transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-accent transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-accent transition-colors">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-12 border-t border-border flex flex-col md:flex-row justify-between items-center gap-6">
            <p className="text-text-secondary text-sm">
              © 2026 Paymigo Technologies Pvt Ltd. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-xs font-bold text-text-secondary">
                <div className="w-2 h-2 rounded-full bg-success" /> System Status: Operational
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
