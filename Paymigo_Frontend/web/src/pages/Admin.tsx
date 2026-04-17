import React, { useState, useEffect } from 'react';
import { collection, query, where, getDocs, updateDoc, doc, orderBy, Timestamp, addDoc, getDoc, increment } from 'firebase/firestore';
import { useNavigate } from 'react-router-dom';
import { db } from '../firebase';
import { useAuth } from '../App';
import { CheckCircle, XCircle, Clock, AlertCircle, FileText, User, IndianRupee, Search, Filter, Zap, ShieldCheck, Info, MessageSquare, MapPin } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { isAdminUser } from '@/lib/utils';

interface Claim {
  id: string;
  workerId: string;
  workerName: string;
  workerCity?: string;
  workerZone?: string;
  type: string;
  description: string;
  statement: string;
  amount: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  adminComment?: string;
  createdAt: any;
}

const Admin = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [adminComment, setAdminComment] = useState('');
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [claimType, setClaimType] = useState('ALL');
  const [cityZone, setCityZone] = useState('');
  const [checklist, setChecklist] = useState({
    statementVerified: false,
    amountValid: false,
    policyActive: false
  });
  const [checklistError, setChecklistError] = useState<string | null>(null);

  const isAdmin = isAdminUser(user?.email);

  useEffect(() => {
    if (isAdmin) {
      fetchClaims();
    }
  }, [isAdmin, filter]);

  useEffect(() => {
    // Reset checklist when selected claim changes
    setChecklist({
      statementVerified: false,
      amountValid: false,
      policyActive: false
    });
    setAdminComment('');
    setChecklistError(null);
  }, [selectedClaim]);

  const fetchClaims = async () => {
    setLoading(true);
    try {
      let q = query(collection(db, 'claims'), orderBy('createdAt', 'desc'));
      if (filter !== 'ALL') {
        q = query(collection(db, 'claims'), where('status', '==', filter), orderBy('createdAt', 'desc'));
      }
      const querySnapshot = await getDocs(q);
      const claimsData = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      })) as Claim[];
      setClaims(claimsData);
    } catch (error) {
      console.error("Error fetching claims:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (claimId: string, newStatus: 'APPROVED' | 'REJECTED') => {
    if (newStatus === 'APPROVED' && (!checklist.statementVerified || !checklist.amountValid || !checklist.policyActive)) {
      setChecklistError('Complete all 3 checklist items before approving.');
      return;
    }
    setChecklistError(null);

    try {
      const claimRef = doc(db, 'claims', claimId);
      const claim = claims.find(c => c.id === claimId);
      if (!claim) return;

      await updateDoc(claimRef, {
        status: newStatus,
        adminComment: adminComment,
        updatedAt: Timestamp.now()
      });
      
      // Create notification for the worker
      await addDoc(collection(db, 'notifications'), {
        workerId: claim.workerId,
        title: `Claim ${newStatus === 'APPROVED' ? 'Approved' : 'Rejected'}`,
        message: newStatus === 'APPROVED' 
          ? `Your claim for ${claim.type} of ₹${claim.amount} has been approved. The amount has been added to your wallet.`
          : `Your claim for ${claim.type} has been rejected. Reason: ${adminComment || 'No comment provided.'}`,
        type: newStatus === 'APPROVED' ? 'SUCCESS' : 'DANGER',
        read: false,
        createdAt: Timestamp.now()
      });

      if (newStatus === 'APPROVED') {
        // Update worker's wallet balance
        const walletRef = doc(db, 'wallets', claim.workerId);
        const walletSnap = await getDoc(walletRef);
        
        if (walletSnap.exists()) {
          const currentBalance = walletSnap.data().availableBalance || 0;
          const newBalance = currentBalance + claim.amount;

          await updateDoc(walletRef, {
            availableBalance: increment(claim.amount),
            totalEarned: increment(claim.amount)
          });

          // Record transaction
          await addDoc(collection(db, 'transactions'), {
            workerId: claim.workerId,
            type: 'CREDIT',
            amount: claim.amount,
            description: `Insurance Claim Payout: ${claim.type}`,
            balanceAfter: newBalance,
            createdAt: Timestamp.now()
          });
        }
      }
      
      setClaims(prev => prev.map(c => c.id === claimId ? { ...c, status: newStatus, adminComment } : c));
      setSelectedClaim(null);
      setAdminComment('');
      fetchClaims();
    } catch (error) {
      console.error("Error updating claim status:", error);
    }
  };

  if (!isAdmin) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-6 text-center">
        <AlertCircle className="w-16 h-16 text-danger mb-4" />
        <h1 className="text-3xl font-display mb-2 text-text-primary">Access Denied</h1>
        <p className="text-text-secondary max-w-md">
          You do not have administrative privileges to access this portal. If you believe this is an error, please contact support.
        </p>
        <button 
          onClick={() => navigate('/')}
          className="mt-6 px-8 py-3 bg-accent text-white rounded-xl font-bold hover:scale-105 transition-all shadow-lg shadow-accent/20 gradient-bg"
        >
          Return Home
        </button>
      </div>
    );
  }

  const filteredClaims = claims.filter(c => {
    const matchesSearch = c.workerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id.toLowerCase().includes(searchTerm.toLowerCase());
    
    const claimDate = new Date(c.createdAt?.toDate?.() || c.createdAt);
    const matchesStartDate = !startDate || claimDate >= new Date(startDate);
    const matchesEndDate = !endDate || claimDate <= new Date(new Date(endDate).setHours(23, 59, 59, 999));
    
    const matchesType = claimType === 'ALL' || c.type === claimType;
    
    const matchesCityZone = !cityZone || 
      c.workerCity?.toLowerCase().includes(cityZone.toLowerCase()) || 
      c.workerZone?.toLowerCase().includes(cityZone.toLowerCase());

    return matchesSearch && matchesStartDate && matchesEndDate && matchesType && matchesCityZone;
  });

  return (
    <div className="min-h-screen bg-surface p-6 md:p-10">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
            <div>
              <h1 className="text-4xl font-display mb-2 text-text-primary">Admin Portal</h1>
              <p className="text-text-secondary">Manage and verify insurance claims from delivery partners.</p>
            </div>
            
            <div className="flex bg-white border border-border rounded-xl p-1">
              {(['PENDING', 'APPROVED', 'REJECTED', 'ALL'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    filter === f ? 'bg-accent text-white shadow-md' : 'text-text-secondary hover:bg-surface'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Advanced Filters */}
          <div className="glass-card p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest ml-1">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                <input 
                  type="text" 
                  placeholder="Name, Type, ID..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-full"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest ml-1">Claim Type</label>
              <select 
                value={claimType}
                onChange={(e) => setClaimType(e.target.value)}
                className="w-full"
              >
                <option value="ALL">All Types</option>
                <option value="Income Protection">Income Protection</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest ml-1">City / Zone</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                <input 
                  type="text" 
                  placeholder="e.g. Chennai" 
                  value={cityZone}
                  onChange={(e) => setCityZone(e.target.value)}
                  className="pl-10 w-full"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest ml-1">Start Date</label>
              <input 
                type="date" 
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest ml-1">End Date</label>
              <input 
                type="date" 
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full"
              />
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Claims List */}
          <div className="lg:col-span-2 space-y-4">
            {loading ? (
              <div className="flex justify-center py-20">
                <div className="w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            ) : filteredClaims.length === 0 ? (
              <div className="glass-card p-20 text-center">
                <FileText className="w-12 h-12 text-border mx-auto mb-4" />
                <p className="text-text-secondary">No claims found matching your criteria.</p>
                {(searchTerm || startDate || endDate || claimType !== 'ALL' || cityZone) && (
                  <button 
                    onClick={() => {
                      setSearchTerm('');
                      setStartDate('');
                      setEndDate('');
                      setClaimType('ALL');
                      setCityZone('');
                    }}
                    className="mt-4 text-accent text-xs font-bold hover:underline"
                  >
                    Clear all filters
                  </button>
                )}
              </div>
            ) : (
              filteredClaims.map((claim) => (
                <motion.div 
                  layoutId={claim.id}
                  key={claim.id}
                  onClick={() => setSelectedClaim(claim)}
                  className={`glass-card p-6 cursor-pointer transition-all hover:shadow-2xl hover:-translate-y-1 border-l-4 ${
                    claim.status === 'PENDING' ? 'border-l-warning' : 
                    claim.status === 'APPROVED' ? 'border-l-success' : 'border-l-danger'
                  } ${selectedClaim?.id === claim.id ? 'ring-2 ring-accent' : ''}`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-surface flex items-center justify-center">
                        <User className="w-5 h-5 text-text-secondary" />
                      </div>
                      <div>
                        <h3 className="font-bold text-text-primary">{claim.workerName}</h3>
                        <p className="text-[10px] text-text-secondary flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {claim.workerZone || 'Unknown Zone'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-accent font-bold mb-1">
                        <IndianRupee className="w-4 h-4" />
                        <span>{claim.amount.toLocaleString()}</span>
                      </div>
                      <span className={`text-[10px] font-black px-2 py-1 rounded-full uppercase tracking-widest ${
                        claim.status === 'PENDING' ? 'bg-warning/10 text-warning' : 
                        claim.status === 'APPROVED' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                      }`}>
                        {claim.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6 text-sm text-text-secondary">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-accent" />
                      <span>{claim.type}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>{new Date(claim.createdAt?.toDate?.() || claim.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>

          {/* Claim Details / Action Panel */}
          <div className="lg:col-span-1">
            <AnimatePresence mode="wait">
              {selectedClaim ? (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  className="glass-card p-8 sticky top-24"
                >
                  <div className="flex justify-between items-start mb-6">
                    <h2 className="text-2xl font-display text-text-primary">Claim Details</h2>
                    <button onClick={() => setSelectedClaim(null)} className="p-1 hover:bg-surface rounded-lg transition-colors">
                      <XCircle className="w-6 h-6 text-text-secondary" />
                    </button>
                  </div>

                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-surface rounded-xl">
                        <label className="text-[10px] uppercase tracking-widest font-black text-text-secondary mb-1 block">Claim Type</label>
                        <p className="font-bold text-text-primary">{selectedClaim.type}</p>
                      </div>
                      <div className="p-3 bg-surface rounded-xl">
                        <label className="text-[10px] uppercase tracking-widest font-black text-text-secondary mb-1 block">Amount</label>
                        <p className="font-bold text-accent flex items-center gap-1">
                          <IndianRupee className="w-3 h-3" />
                          {selectedClaim.amount.toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div className="p-3 bg-surface rounded-xl">
                      <label className="text-[10px] uppercase tracking-widest font-black text-text-secondary mb-1 block">Worker Location</label>
                      <p className="font-bold text-text-primary flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-accent" />
                        {selectedClaim.workerZone || 'Unknown Zone'}
                      </p>
                    </div>

                    <div>
                      <label className="text-[10px] uppercase tracking-widest font-black text-text-secondary mb-2 block">Worker Description</label>
                      <div className="p-4 bg-surface rounded-xl border border-border/50">
                        <p className="text-sm text-text-secondary leading-relaxed">{selectedClaim.description}</p>
                      </div>
                    </div>

                    <div>
                      <label className="text-[10px] uppercase tracking-widest font-black text-accent mb-2 block flex items-center gap-2">
                        <MessageSquare className="w-3 h-3" />
                        Legible Statement
                      </label>
                      <div className="p-4 bg-accent/5 rounded-xl border border-accent/20">
                        <p className="text-sm italic text-text-primary leading-relaxed">"{selectedClaim.statement}"</p>
                      </div>
                    </div>

                    {selectedClaim.status === 'PENDING' && (
                      <div className="pt-6 border-t border-border">
                        <label className="text-[10px] uppercase tracking-widest font-black text-text-secondary mb-4 block flex items-center gap-2">
                          <ShieldCheck className="w-3 h-3" />
                          Verification Checklist
                        </label>
                        <div className="space-y-3 mb-6">
                          <label className="flex items-center gap-3 p-3 bg-surface rounded-xl cursor-pointer hover:bg-white/50 transition-colors">
                            <input 
                              type="checkbox" 
                              checked={checklist.statementVerified}
                              onChange={(e) => setChecklist(prev => ({ ...prev, statementVerified: e.target.checked }))}
                              className="w-5 h-5 rounded-lg border-border text-accent focus:ring-accent"
                            />
                            <span className="text-sm font-medium text-text-primary">Statement is legible and valid</span>
                          </label>
                          <label className="flex items-center gap-3 p-3 bg-surface rounded-xl cursor-pointer hover:bg-white/50 transition-colors">
                            <input 
                              type="checkbox" 
                              checked={checklist.amountValid}
                              onChange={(e) => setChecklist(prev => ({ ...prev, amountValid: e.target.checked }))}
                              className="w-5 h-5 rounded-lg border-border text-accent focus:ring-accent"
                            />
                            <span className="text-sm font-medium text-text-primary">Claimed amount matches policy limits</span>
                          </label>
                          <label className="flex items-center gap-3 p-3 bg-surface rounded-xl cursor-pointer hover:bg-white/50 transition-colors">
                            <input 
                              type="checkbox" 
                              checked={checklist.policyActive}
                              onChange={(e) => setChecklist(prev => ({ ...prev, policyActive: e.target.checked }))}
                              className="w-5 h-5 rounded-lg border-border text-accent focus:ring-accent"
                            />
                            <span className="text-sm font-medium text-text-primary">Worker policy was active during incident</span>
                          </label>
                        </div>

                        <div className="space-y-4">
                          <label className="text-[10px] uppercase tracking-widest font-black text-text-secondary mb-2 block">Admin Feedback</label>
                          <textarea 
                            placeholder="Add reason for approval/rejection..."
                            value={adminComment}
                            onChange={(e) => setAdminComment(e.target.value)}
                            className="w-full h-24 text-sm p-4 bg-white border border-border rounded-xl outline-none focus:border-accent"
                          />
                          {checklistError && (
                            <p className="text-[11px] font-bold text-danger flex items-center gap-1 mb-2">
                              <AlertCircle className="w-3 h-3" /> {checklistError}
                            </p>
                          )}
                          <div className="grid grid-cols-2 gap-4">
                            <button
                              onClick={() => handleUpdateStatus(selectedClaim.id, 'REJECTED')}
                              className="flex items-center justify-center gap-2 py-4 bg-danger/10 text-danger rounded-xl font-bold hover:bg-danger hover:text-white transition-all"
                            >
                              <XCircle className="w-4 h-4" />
                              Reject
                            </button>
                            <button
                              onClick={() => handleUpdateStatus(selectedClaim.id, 'APPROVED')}
                              disabled={!checklist.statementVerified || !checklist.amountValid || !checklist.policyActive}
                              className="flex items-center justify-center gap-2 py-4 bg-success text-white rounded-xl font-bold hover:scale-105 transition-all shadow-lg shadow-success/20 disabled:opacity-50 disabled:scale-100 disabled:cursor-not-allowed"
                            >
                              <CheckCircle className="w-4 h-4" />
                              Approve
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {selectedClaim.status !== 'PENDING' && (
                      <div className="pt-6 border-t border-border">
                        <div className={`p-6 rounded-2xl flex items-start gap-4 ${
                          selectedClaim.status === 'APPROVED' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                        }`}>
                          <div className={`p-2 rounded-lg ${
                            selectedClaim.status === 'APPROVED' ? 'bg-success/20' : 'bg-danger/20'
                          }`}>
                            {selectedClaim.status === 'APPROVED' ? <CheckCircle className="w-6 h-6" /> : <XCircle className="w-6 h-6" />}
                          </div>
                          <div>
                            <p className="font-black text-xs uppercase tracking-widest mb-1">Claim {selectedClaim.status}</p>
                            <p className="text-sm font-medium opacity-90 leading-relaxed">
                              {selectedClaim.adminComment || "No additional feedback provided."}
                            </p>
                            <div className="mt-4 flex items-center gap-2 text-[10px] font-bold opacity-60">
                              <Info className="w-3 h-3" />
                              Processed on {new Date().toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              ) : (
                <div className="glass-card p-10 text-center flex flex-col items-center justify-center min-h-[400px]">
                  <div className="w-16 h-16 bg-surface rounded-full flex items-center justify-center mb-4">
                    <Filter className="w-8 h-8 text-border" />
                  </div>
                  <h3 className="font-bold text-text-primary mb-2">No Claim Selected</h3>
                  <p className="text-sm text-text-secondary">Select a claim from the list to view full details and take action.</p>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Admin;
