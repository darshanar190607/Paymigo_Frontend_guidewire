import express from 'express';
import Razorpay from 'razorpay';
import crypto from 'crypto';
import prisma from '../lib/prisma.js';
import { requireAuth } from '../middleware/authMiddleware.js';

const router = express.Router();

// Initialize Razorpay instance
const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID,
  key_secret: process.env.RAZORPAY_KEY_SECRET,
});

// ── POST /payment/create-order ────────────────────────────────────────────────
// Creates a Razorpay order for premium payment
router.post('/create-order', requireAuth, async (req, res) => {
  const { amount, currency = 'INR', receipt, notes } = req.body;

  if (!amount) {
    return res.status(400).json({ error: 'Amount is required' });
  }

  try {
    const options = {
      amount: amount * 100, // Razorpay expects amount in paise (1 INR = 100 paise)
      currency,
      receipt: receipt || `receipt_${Date.now()}`,
      notes: notes || {},
    };

    const order = await razorpay.orders.create(options);

    res.json({
      success: true,
      order_id: order.id,
      amount: order.amount,
      currency: order.currency,
      key_id: process.env.RAZORPAY_KEY_ID, // Send public key to frontend
    });
  } catch (error) {
    console.error('Razorpay order creation error:', error);
    res.status(500).json({ error: 'Failed to create payment order' });
  }
});

// ── POST /payment/verify ──────────────────────────────────────────────────────
// Verifies Razorpay payment signature
router.post('/verify', async (req, res) => {
  const { razorpay_order_id, razorpay_payment_id, razorpay_signature, workerId, planId, weeklyPremium } = req.body;

  console.log('Payment verification request:', { razorpay_order_id, razorpay_payment_id, workerId, planId });

  if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature) {
    console.error('Missing parameters:', { razorpay_order_id, razorpay_payment_id, razorpay_signature });
    return res.status(400).json({ error: 'Missing payment verification parameters' });
  }

  try {
    // Verify signature
    const body = razorpay_order_id + '|' + razorpay_payment_id;
    const expectedSignature = crypto
      .createHmac('sha256', process.env.RAZORPAY_KEY_SECRET)
      .update(body.toString())
      .digest('hex');

    console.log('Signature verification:', { 
      expected: expectedSignature, 
      received: razorpay_signature,
      match: expectedSignature === razorpay_signature 
    });

    const isAuthentic = expectedSignature === razorpay_signature;

    if (!isAuthentic) {
      console.error('Invalid signature');
      return res.status(400).json({ error: 'Invalid payment signature' });
    }

    console.log('Payment verified successfully');

    // Payment verified successfully
    // Create/update policy in database
    if (workerId && planId && weeklyPremium) {
      try {
        const worker = await prisma.worker.findFirst({
          where: { OR: [{ id: workerId }, { firebaseUid: workerId }] },
        });

        if (worker) {
          console.log('Worker found:', worker.id);
          
          // Deactivate existing policies
          await prisma.policy.updateMany({
            where: { workerId: worker.id, isActive: true },
            data: { isActive: false, endDate: new Date() },
          });

          // Create new policy
          const newPolicy = await prisma.policy.create({
            data: {
              workerId: worker.id,
              tier: planId,
              weeklyPremium: weeklyPremium,
              loyaltyPercent: 0,
              isActive: true,
              startDate: new Date(),
            },
          });
          
          console.log('New policy created:', newPolicy.id);
        } else {
          console.warn('Worker not found:', workerId);
        }
      } catch (dbError) {
        console.error('Database error:', dbError);
        // Don't fail the payment verification if DB update fails
      }
    }

    res.json({
      success: true,
      message: 'Payment verified successfully',
      payment_id: razorpay_payment_id,
      order_id: razorpay_order_id,
    });
  } catch (error) {
    console.error('Payment verification error:', error);
    res.status(500).json({ error: 'Payment verification failed', details: error.message });
  }
});

// ── GET /payment/status/:paymentId ────────────────────────────────────────────
// Fetches payment status from Razorpay
router.get('/status/:paymentId', requireAuth, async (req, res) => {
  const { paymentId } = req.params;

  try {
    const payment = await razorpay.payments.fetch(paymentId);
    res.json({
      success: true,
      payment: {
        id: payment.id,
        amount: payment.amount / 100, // Convert paise to INR
        currency: payment.currency,
        status: payment.status,
        method: payment.method,
        created_at: payment.created_at,
      },
    });
  } catch (error) {
    console.error('Payment status fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch payment status' });
  }
});

export default router;
