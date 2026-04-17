import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import workerRoutes from "./routes/worker.js";
import premiumRoutes from "./routes/premium.js";
import authRoutes from "./routes/auth.js";
import triggerRoutes from "./routes/triggers.js";
import aiRoutes from "./routes/ai.js";
import weatherRoutes from "./routes/weather.js";
import payoutRoutes from "./routes/payouts.js";
import orchestratorRoutes from "./routes/orchestrator.js";
import pricingRoutes from "./routes/pricing.js";
import geotruthRoutes from "./routes/geotruth.js";
import fraudRoutes from "./routes/fraud.js";
import analyticsRoutes from "./routes/analytics.js";
import dashboardRoutes from "./routes/dashboard.js";
import paymentRoutes from "./routes/payment.js";
import fraudMockRoutes from "./routes/fraud-mock.js";
import walletRoutes from "./routes/wallet.js";
import nlpRoutes from "./routes/nlp.js";
import forecastOpsRoutes from "./routes/forecast-ops.js";
import claimsRoutes from "./routes/claims.js";
import { requireAuth } from "./middleware/authMiddleware.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());


// --- HACKATHON QUICK WIN: Keep-Alive Ping (Prevents Sleep) ---
setInterval(() => {
  fetch(`http://localhost:${process.env.PORT || 3000}/`).catch(() => {});
}, 10 * 60 * 1000);

app.use("/auth", authRoutes);
app.use("/workers", requireAuth, workerRoutes);
app.use("/premium", requireAuth, premiumRoutes);
app.use("/api/triggers", requireAuth, triggerRoutes);
app.use("/api/ai", requireAuth, aiRoutes);
app.use("/api/weather", requireAuth, weatherRoutes);
app.use("/api/payouts", requireAuth, payoutRoutes);
app.use("/api/trigger", requireAuth, orchestratorRoutes);
app.use("/pricing", requireAuth, pricingRoutes);
app.use("/geotruth", requireAuth, geotruthRoutes);
app.use("/fraud", requireAuth, fraudRoutes);
app.use("/api/analytics", requireAuth, analyticsRoutes);
app.use("/dashboard", requireAuth, dashboardRoutes);
app.use("/payment", requireAuth, paymentRoutes);
app.use("/fraud-mock", requireAuth, fraudMockRoutes);
app.use("/wallet", requireAuth, walletRoutes);
app.use("/api/nlp", requireAuth, nlpRoutes);
app.use("/api/claims", requireAuth, claimsRoutes);
app.use("/api", forecastOpsRoutes);

app.get("/", (req, res) => {
  res.send("Backend Running 🚀");
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`);
});
