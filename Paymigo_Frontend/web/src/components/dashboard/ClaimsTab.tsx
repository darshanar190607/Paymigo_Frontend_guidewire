import React, { useState, useEffect } from 'react';
import { PlusCircle, FileText, IndianRupee } from 'lucide-react';
import { cn } from '@/lib/utils';
import { db } from '../../firebase';
import { collection, addDoc, Timestamp, query, where, onSnapshot } from 'firebase/firestore';
import type { User } from 'firebase/auth';
import type { Worker, Claim } from '../../types/dashboard';

interface ClaimsTabProps {
  user: User;
  workerData: Worker | null;
}

const ClaimsTab = ({ user, workerData }: ClaimsTabProps) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [newClaim, setNewClaim] = useState({
    type: 'Income Protection',
    description: '',
    statement: '',
    amount: ''
  });

  useEffect(() => {
    if (!user) return;
    const q = query(collection(db, 'claims'), where('workerId', '==', user.uid));
    const unsub = onSnapshot(q, (snapshot) => {
      const fetchedClaims = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Claim));
      fetchedClaims.sort((a, b) => {
        const timeA = a.createdAt?.toMillis?.() || 0;
        const timeB = b.createdAt?.toMillis?.() || 0;
        return timeB - timeA;
      });
      setClaims(fetchedClaims);
    }, (error) => {
      console.error('Error fetching claims:', error);
    });
    return () => unsub();
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClaim.description || !newClaim.statement || !newClaim.amount) return;

    setIsSubmitting(true);
    setSubmitMessage(null);
    try {
      await addDoc(collection(db, 'claims'), {
        workerId: user.uid,
        workerName: workerData?.name || user.displayName || 'Worker',
        workerCity: workerData?.city || '',
        workerZone: workerData?.zone || '',
        ...newClaim,
        amount: parseFloat(newClaim.amount),
        status: 'PENDING',
        createdAt: Timestamp.now()
      });
      setNewClaim({ type: 'Income Protection', description: '', statement: '', amount: '' });
      setSubmitMessage({ type: 'success', text: 'Claim submitted! Admin will review it shortly.' });
    } catch (error) {
      console.error('Error submitting claim:', error);
      setSubmitMessage({ type: 'error', text: 'Failed to submit claim. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="grid lg:grid-cols-3 gap-8">
        {/* New Claim Form */}
        <div className="lg:col-span-1">
          <div className="glass-card p-8 sticky top-24">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <PlusCircle className="w-5 h-5 text-accent" /> New Claim
            </h3>

            {submitMessage && (
              <div className={cn(
                'mb-4 p-3 rounded-xl text-xs font-bold',
                submitMessage.type === 'success' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
              )}>
                {submitMessage.text}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Claim Type</label>
                <select
                  value={newClaim.type}
                  onChange={(e) => setNewClaim({ ...newClaim, type: e.target.value })}
                  className="w-full"
                >
                  <option>Income Protection</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Claim Amount (₹)</label>
                <input
                  type="number"
                  placeholder="e.g. 1500"
                  value={newClaim.amount}
                  onChange={(e) => setNewClaim({ ...newClaim, amount: e.target.value })}
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Description</label>
                <textarea
                  placeholder="What happened?"
                  value={newClaim.description}
                  onChange={(e) => setNewClaim({ ...newClaim, description: e.target.value })}
                  className="w-full h-24 text-sm"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-accent uppercase tracking-widest">Legible Statement</label>
                <textarea
                  placeholder="Provide a clear, detailed statement for verification..."
                  value={newClaim.statement}
                  onChange={(e) => setNewClaim({ ...newClaim, statement: e.target.value })}
                  className="w-full h-32 text-sm border-accent/30 focus:border-accent"
                />
                <p className="text-[10px] text-text-secondary italic">This statement is critical for admin verification.</p>
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-4 bg-accent text-white rounded-xl font-bold hover:glow-accent transition-all disabled:opacity-50"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Claim'}
              </button>
            </form>
          </div>
        </div>

        {/* Claims History */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xl font-bold mb-4">Your Claims History</h3>
          {claims.length === 0 ? (
            <div className="glass-card p-20 text-center">
              <FileText className="w-12 h-12 text-border mx-auto mb-4" />
              <p className="text-text-secondary">You haven't submitted any claims yet.</p>
            </div>
          ) : (
            claims.map((claim) => (
              <div key={claim.id} className="glass-card p-6 border-l-4 border-l-accent">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="font-bold text-text-primary">{claim.type}</h4>
                    <p className="text-xs text-text-secondary">
                      {new Date(claim.createdAt?.toDate?.() || claim.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-accent font-bold flex items-center gap-1">
                      <IndianRupee className="w-3 h-3" />{claim.amount}
                    </div>
                    <span className={cn(
                      'text-[10px] font-black px-2 py-1 rounded-full uppercase tracking-widest',
                      claim.status === 'PENDING' ? 'bg-warning/10 text-warning' :
                      claim.status === 'APPROVED' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                    )}>
                      {claim.status}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-text-secondary line-clamp-2 mb-2">{claim.description}</p>
                {claim.adminComment && (
                  <div className="mt-4 p-3 bg-surface rounded-lg border border-border/50">
                    <p className="text-[10px] font-black text-text-secondary uppercase mb-1">Admin Comment</p>
                    <p className="text-xs italic text-text-primary">"{claim.adminComment}"</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ClaimsTab;
