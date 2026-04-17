import express from 'express';
import prisma from '../lib/prisma.js';
import { requireAuth } from '../middleware/authMiddleware.js';
import admin from 'firebase-admin';

const router = express.Router();

// ── POST /wallet/withdraw ─────────────────────────────────────────────────────
// Withdraw funds from GigWallet
router.post('/withdraw', requireAuth, async (req, res) => {
  const { workerId, amount, upiId } = req.body;

  if (!workerId || !amount) {
    return res.status(400).json({ error: 'workerId and amount are required' });
  }

  if (amount <= 0) {
    return res.status(400).json({ error: 'Amount must be greater than 0' });
  }

  try {
    // Get wallet from Firestore
    const db = admin.firestore();
    const walletRef = db.collection('wallets').doc(workerId);
    const walletDoc = await walletRef.get();

    if (!walletDoc.exists) {
      return res.status(404).json({ error: 'Wallet not found' });
    }

    const walletData = walletDoc.data();
    const availableBalance = walletData.availableBalance || 0;

    // Check if sufficient balance
    if (amount > availableBalance) {
      return res.status(400).json({ 
        error: 'Insufficient balance',
        availableBalance,
        requestedAmount: amount,
      });
    }

    // Update wallet balance
    const newBalance = availableBalance - amount;
    await walletRef.update({
      availableBalance: newBalance,
      lastWithdrawal: new Date(),
      totalWithdrawn: (walletData.totalWithdrawn || 0) + amount,
    });

    // Create withdrawal transaction record
    await db.collection('transactions').add({
      workerId,
      type: 'WITHDRAWAL',
      amount,
      upiId: upiId || 'Not provided',
      status: 'COMPLETED',
      balanceBefore: availableBalance,
      balanceAfter: newBalance,
      createdAt: new Date(),
      processedAt: new Date(),
    });

    res.json({
      success: true,
      message: 'Withdrawal successful',
      withdrawnAmount: amount,
      newBalance,
      transactionId: `TXN_${Date.now()}`,
    });
  } catch (error) {
    console.error('Withdrawal error:', error);
    res.status(500).json({ error: 'Withdrawal failed', details: error.message });
  }
});

// ── GET /wallet/balance/:workerId ─────────────────────────────────────────────
// Get wallet balance
router.get('/balance/:workerId', requireAuth, async (req, res) => {
  const { workerId } = req.params;

  try {
    const db = admin.firestore();
    const walletDoc = await db.collection('wallets').doc(workerId).get();

    if (!walletDoc.exists) {
      return res.json({
        availableBalance: 0,
        totalEarned: 0,
        totalWithdrawn: 0,
      });
    }

    const walletData = walletDoc.data();
    res.json({
      availableBalance: walletData.availableBalance || 0,
      totalEarned: walletData.totalEarned || 0,
      totalWithdrawn: walletData.totalWithdrawn || 0,
      lastWithdrawal: walletData.lastWithdrawal || null,
    });
  } catch (error) {
    console.error('Balance fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch balance' });
  }
});

// ── GET /wallet/transactions/:workerId ────────────────────────────────────────
// Get transaction history
router.get('/transactions/:workerId', requireAuth, async (req, res) => {
  const { workerId } = req.params;
  const { limit = 10 } = req.query;

  try {
    const db = admin.firestore();
    const snapshot = await db.collection('transactions')
      .where('workerId', '==', workerId)
      .orderBy('createdAt', 'desc')
      .limit(parseInt(limit))
      .get();

    const transactions = [];
    snapshot.forEach(doc => {
      transactions.push({
        id: doc.id,
        ...doc.data(),
        createdAt: doc.data().createdAt?.toDate?.() || doc.data().createdAt,
      });
    });

    res.json({
      transactions,
      count: transactions.length,
    });
  } catch (error) {
    console.error('Transaction history error:', error);
    res.status(500).json({ error: 'Failed to fetch transactions' });
  }
});

export default router;
