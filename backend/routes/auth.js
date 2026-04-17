import express from "express";
import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";
import prisma from "../lib/prisma.js";
import initFirebaseAdmin from "../lib/firebaseAdmin.js";

const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET || "fallback_secret";

const admin = initFirebaseAdmin();

// Helper to generate JWT
const generateToken = (worker) => {
  return jwt.sign(
    { workerId: worker.id, email: worker.email, role: "worker" },
    JWT_SECRET,
    { expiresIn: "7d" }
  );
};

// 1. Email/Password Register
router.post("/register", async (req, res) => {
  try {
    const { email, password, phone, name, pincode, zoneId } = req.body;
    
    if (!email || !password || !phone || !pincode || !zoneId) {
      return res.status(400).json({ error: "Missing required fields." });
    }

    const existingUser = await prisma.worker.findFirst({
      where: { OR: [{ email }, { phone }] }
    });

    if (existingUser) {
      return res.status(400).json({ error: "User with this email or phone already exists." });
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const riskTier = 1; 
    
    if (zoneId === 'default') {
      await prisma.zone.upsert({
        where: { pincode: '000000' },
        update: {},
        create: {
          id: 'default',
          name: 'Dummy Zone',
          city: 'Unknown',
          pincode: '000000',
          riskTier: 1,
          riskMultiplier: 1.0,
        }
      });
    }

    const worker = await prisma.worker.create({
      data: {
        email,
        phone,
        passwordHash,
        name,
        pincode,
        zoneId,
        riskTier
      }
    });

    const firebaseToken = await admin.auth().createCustomToken(worker.id.toString());
    const token = generateToken(worker);
    return res.json({ token, worker, firebaseToken });
  } catch (error) {
    console.error("Detailed Register Error:", error);
    return res.status(500).json({ 
      error: "Internal server error.", 
      details: error.message,
      code: error.code 
    });
  }
});

// 2. Email/Password Login
router.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: "Email and password are required." });
    }

    const worker = await prisma.worker.findUnique({ where: { email } });
    if (!worker) {
      console.log(`Login failed: User not found for email: ${email}`);
      return res.status(401).json({ error: "Invalid credentials." });
    }

    if (!worker.passwordHash) {
      console.log(`Login failed: User ${email} exists but has no password (likely a Google-only user)`);
      return res.status(401).json({ error: "Please log in with Google for this account." });
    }

    const isMatch = await bcrypt.compare(password, worker.passwordHash);
    if (!isMatch) {
      console.log(`Login failed: Incorrect password for user: ${email}`);
      return res.status(401).json({ error: "Invalid credentials." });
    }

    let firebaseToken = null;
    try {
      firebaseToken = await admin.auth().createCustomToken(worker.id.toString());
    } catch (firebaseError) {
      console.warn("⚠️ Firebase Custom Token failed, but proceeding with JWT:", firebaseError.message);
      // We still provide the worker and token so they can log in
    }

    const token = generateToken(worker);
    return res.json({ token, worker, firebaseToken });
  } catch (error) {
    console.error("Detailed Login Error:", error);
    res.status(500).json({ 
      error: "Internal server error.", 
      message: error.message 
    });
  }
});

// 3. Google Login (via Firebase ID Token)
router.post("/google", async (req, res) => {
  try {
    const { idToken, pincode, zoneId, phone } = req.body; 
    
    if (!idToken) {
      return res.status(400).json({ error: "Missing Firebase ID token." });
    }

    const decodedToken = await admin.auth().verifyIdToken(idToken);
    const { uid, email, name } = decodedToken;

    if (!email) {
      return res.status(400).json({ error: "Google account does not have an email attached." });
    }

    let worker = await prisma.worker.findFirst({
      where: {
        OR: [{ firebaseUid: uid }, { email: email }]
      }
    });

    if (!worker) {
      const finalPhone = phone || 'PENDING_' + Math.random().toString(36).substring(7);
      const finalPincode = pincode || '000000';

      await prisma.zone.upsert({
        where: { pincode: '000000' },
        update: {},
        create: {
          id: 'default',
          name: 'Dummy Zone',
          city: 'Unknown',
          pincode: '000000',
          riskTier: 1,
          riskMultiplier: 1.0,
        }
      });

      worker = await prisma.worker.create({
        data: {
          email,
          name,
          firebaseUid: uid,
          phone: finalPhone,
          pincode: finalPincode,
          zoneId: 'default',
          riskTier: 1
        }
      });
    } else {
      if (!worker.firebaseUid) {
        worker = await prisma.worker.update({
          where: { id: worker.id },
          data: { firebaseUid: uid }
        });
      }
    }

    const firebaseToken = await admin.auth().createCustomToken(worker.id.toString());
    const token = generateToken(worker);
    return res.json({ token, worker, firebaseToken });
  } catch (error) {
    console.error("Detailed Google Auth Error:", error);
    return res.status(401).json({ 
      error: "Unauthorized. Invalid Google Token.",
      details: error.message 
    });
  }
});

export default router;
