import express from 'express';
import prisma from '../lib/prisma.js';
import admin from 'firebase-admin';

const router = express.Router();

router.post('/trigger-payout', async (req, res) => {
  const { workerId, rainfall, threshold, mode } = req.body;

  try {
    const db = admin.firestore();
    const isFraudMode = mode === 'fraud';
    
    // 1. Check if a payout was already triggered recently for this worker
    // (To prevent duplicate payouts for the same storm)
    const recentClaims = await db.collection('claims')
      .where('workerId', '==', workerId)
      .where('type', '==', 'Income Protection')
      .where('status', '==', 'APPROVED')
      .limit(1)
      .get();
    
    let alreadyPaid = false;
    const now = new Date();
    recentClaims.forEach(doc => {
      const data = doc.data();
      const createdAt = data.createdAt?.toDate?.() || new Date(data.createdAt);
      if (now.getTime() - createdAt.getTime() < 12 * 60 * 60 * 1000) { // 12 hours
        alreadyPaid = true;
      }
    });

    if (alreadyPaid && !isFraudMode) {
      return res.status(400).json({ error: 'Payout already issued for this event.' });
    }

    // 2. Create Claim in Firestore
    const claimData = {
      workerId,
      workerName: workerId.split('-')[0], // Placeholder
      type: 'Income Protection',
      description: isFraudMode 
        ? `SUSPICIOUS: Automatic trigger during suspected signal anomaly (${rainfall}mm)`
        : `Automatic parametric payout triggered by ${rainfall}mm rainfall (Threshold: ${threshold}mm)`,
      statement: isFraudMode
        ? 'WARNING: Multiple GPS jumps and barometric inconsistencies detected during trigger window.'
        : 'AI-monitored weather trigger detected severe disruption in your zone.',
      amount: 150.0,
      status: isFraudMode ? 'REVIEW' : 'APPROVED',
      fraudScore: isFraudMode ? 0.88 : 0.05,
      spoofProbability: isFraudMode ? 0.95 : 0.02,
      createdAt: admin.firestore.FieldValue.serverTimestamp()
    };

    const claimRef = await db.collection('claims').add(claimData);

    // 3. Update Wallet (ONLY if not fraud mode)
    if (!isFraudMode) {
      const walletRef = db.collection('wallets').doc(workerId);
      await db.runTransaction(async (t) => {
        const walletDoc = await t.get(walletRef);
        if (walletDoc.exists) {
          const currentBalance = walletDoc.data().availableBalance || 0;
          t.update(walletRef, { 
            availableBalance: currentBalance + 150.0,
            totalEarned: (walletDoc.data().totalEarned || 0) + 150.0
          });
        } else {
          t.set(walletRef, {
            workerId,
            availableBalance: 150.0,
            totalEarned: 150.0,
            createdAt: admin.firestore.FieldValue.serverTimestamp()
          });
        }
      });
    }

    // 4. Create Notification
    await db.collection('notifications').add({
      workerId,
      title: isFraudMode ? 'Claim Under Review ⚠️' : 'Payout Triggered! 💸',
      message: isFraudMode
        ? `Suspicious activity detected. Your claim for ₹150 has been sent for manual fraud review.`
        : `Severe rain detected (${rainfall}mm). We've credited ₹150 to your GigWallet instantly.`,
      type: isFraudMode ? 'WARNING' : 'SUCCESS',
      read: false,
      createdAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // 5. Sync with Prisma (SQL) if needed
    if (!isFraudMode) {
      await prisma.transaction?.create({
        data: {
          workerId: workerId, // Ensure this matches your Prisma schema (String or Int)
          type: 'CREDIT',
          amount: 150.0,
          description: 'Auto Weather Payout',
          balanceAfter: 0 
        }
      }).catch(e => console.log('Prisma transaction sync skipped:', e.message));
    }

    res.json({ success: true, claimId: claimRef.id });

  } catch (error) {
    console.error('Trigger Payout Error:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
