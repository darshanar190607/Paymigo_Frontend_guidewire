# PayMigo System Testing Checklist

## 🚀 Pre-Testing Setup

### 1. Environment Setup
```bash
# Backend
cd backend
npm install
npx prisma generate
npx prisma migrate dev

# ML Service
cd ../ml-services/ML-Service
pip install -r requirements.txt
pip install -e Geotruth/

# Frontend
cd ../../Paymigo_Frontend/web
npm install
```

### 2. Environment Variables

**Backend (.env)**
```env
PORT=3000
DATABASE_URL="postgresql://user:password@localhost:5432/paymigo"
JWT_SECRET="your-secret-key"
FIREBASE_PROJECT_ID="paymigo-27412"
```

**Frontend (.env)**
```env
VITE_API_URL=http://localhost:3000
VITE_ML_URL=http://127.0.0.1:8000
VITE_FIREBASE_API_KEY=your-key
VITE_FIREBASE_AUTH_DOMAIN=paymigo-27412.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=paymigo-27412
```

### 3. Start Services
```bash
# Terminal 1 - Backend
cd backend
node server.js

# Terminal 2 - ML Service
cd ml-services/ML-Service
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
cd Paymigo_Frontend/web
npm run dev
```

---

## ✅ Testing Checklist

### Phase 1: ML Service Health Check

#### Test 1.1: ML Service Running
```bash
curl http://127.0.0.1:8000/
```
**Expected:** `{"status": "online", "message": "PayMigo ML Service is running"}`

#### Test 1.2: Health Endpoint
```bash
curl http://127.0.0.1:8000/health/status
```
**Expected:** Service health status

#### Test 1.3: GeoTruth Endpoint Available
```bash
curl http://127.0.0.1:8000/docs
```
**Expected:** FastAPI docs page with `/geotruth/verify` endpoint listed

#### Test 1.4: Fraud Detection
```bash
curl -X POST http://127.0.0.1:8000/fraud/detect \
  -H "Content-Type: application/json" \
  -d '{
    "zone_risk_tier": 2.0,
    "claim_frequency_30d": 1.0,
    "gps_spoof_probability": 0.1,
    "policy_tenure_weeks": 8.0
  }'
```
**Expected:** `{"is_fraud": false, "fraud_probability": <value>}`

#### Test 1.5: LSTM Forecast
```bash
curl -X POST http://127.0.0.1:8000/orchestrator/pipeline/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "zone_1",
    "days": 7
  }'
```
**Expected:** `{"risk_scores": [array of 7 values]}`

---

### Phase 2: Backend API Testing

#### Test 2.1: Backend Running
```bash
curl http://localhost:3000/
```
**Expected:** `"Backend Running 🚀"`

#### Test 2.2: Dashboard Summary (Mock)
```bash
curl "http://localhost:3000/dashboard/summary?workerId=test123" \
  -H "Authorization: Bearer <token>"
```
**Expected:** Dashboard data with zone, risk, trigger, forecast

#### Test 2.3: Pricing Intelligence
```bash
curl "http://localhost:3000/pricing/intelligence?workerId=test123" \
  -H "Authorization: Bearer <token>"
```
**Expected:** 3 plans with pricing + recommendation

#### Test 2.4: GeoTruth Verification
```bash
curl -X POST http://localhost:3000/geotruth/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "workerId": "test123",
    "gps_spoof_probability": 0.15,
    "behavioral_baseline_deviation": 0.2
  }'
```
**Expected:** Trust score, signals, decision

#### Test 2.5: Analytics Forecast
```bash
curl http://localhost:3000/api/analytics/forecast \
  -H "Authorization: Bearer <token>"
```
**Expected:** Global forecast + zone forecasts (no self-referencing error)

#### Test 2.6: Analytics Zones
```bash
curl http://localhost:3000/api/analytics/zones \
  -H "Authorization: Bearer <token>"
```
**Expected:** Zone heatmap data with risk levels

---

### Phase 3: Frontend Integration Testing

#### Test 3.1: Landing Page
- Navigate to `http://localhost:5173/`
- **Expected:** Landing page loads without errors

#### Test 3.2: Login Flow
- Navigate to `/login`
- Attempt Google login
- **Expected:** Redirects to dashboard after auth

#### Test 3.3: Dashboard
- Navigate to `/dashboard`
- **Expected:** 
  - Zone risk card displays
  - Trigger status shows
  - Forecast summary visible
  - Premium amount shown with ₹ symbol

#### Test 3.4: Plans Page
- Navigate to `/plans`
- **Expected:**
  - 3 plan cards display
  - Pricing shown with ₹ symbol
  - Recommendation badge on one plan
  - "Select Plan" buttons functional

#### Test 3.5: Claim Verification
- Navigate to `/claim/verify`
- Fill claim form
- Submit
- **Expected:**
  - Trust score displays (0-100)
  - 7 signal cards show status
  - Timeline updates
  - Action button appears

#### Test 3.6: Risk Analytics (Worker View)
- Login as worker
- Navigate to `/analytics`
- **Expected:**
  - Simplified view with 2 cards
  - Weekly risk outlook
  - Risk status badge

#### Test 3.7: Risk Analytics (Admin View)
- Login as admin
- Navigate to `/admin/analytics`
- **Expected:**
  - 4 metric cards at top
  - Projected Payout shows ₹ symbol (NOT ¥)
  - 7-day forecast chart renders
  - Zone heatmap displays
  - Claim prediction panel
  - Premium impact panel
  - Alerts & insights panel

#### Test 3.8: Fraud Review (Admin)
- Navigate to `/admin/fraud-review`
- **Expected:**
  - Fraud queue displays
  - Claims with high fraud scores shown
  - Review actions available

---

### Phase 4: End-to-End Flow Testing

#### Test 4.1: Complete Claim Flow
1. Worker logs in
2. Navigates to dashboard
3. Sees trigger active
4. Clicks "File Claim"
5. Fills claim form
6. Submits claim
7. **Expected:**
   - Backend calls ML fraud detection
   - GeoTruth verification runs
   - Trust score calculated
   - Decision returned (approved/review/processing)
   - UI updates with result
   - Timeline shows current step

#### Test 4.2: Pricing Selection Flow
1. Worker logs in
2. Navigates to `/plans`
3. Views 3 plan options
4. Sees recommendation
5. Clicks "Select Plan"
6. **Expected:**
   - Backend calls premium engine
   - Policy created in DB
   - Confirmation shown
   - Dashboard updates with new premium

#### Test 4.3: Admin Analytics Flow
1. Admin logs in
2. Navigates to `/admin/analytics`
3. Views forecast
4. **Expected:**
   - Backend calls `/api/analytics/forecast`
   - Backend calls ML LSTM endpoint (NOT self-referencing)
   - 7-day forecast data returned
   - Charts render
   - Zone heatmap populates
   - Insights panel shows alerts

---

### Phase 5: Integration Validation

#### Test 5.1: No Self-Referencing
- Monitor backend logs during analytics page load
- **Expected:** 
  - Backend calls `http://127.0.0.1:8000/orchestrator/pipeline/forecast`
  - NO calls to `http://127.0.0.1:8000/api/analytics/forecast`

#### Test 5.2: Currency Symbol
- Check all pages with monetary values
- **Expected:**
  - Dashboard: ₹ symbol
  - Plans: ₹ symbol
  - Analytics: ₹ symbol (line 241 in RiskAnalytics.tsx)
  - NO ¥ symbols anywhere

#### Test 5.3: RiskAnalytics Routing
- Navigate to `/analytics` (worker)
- Navigate to `/admin/analytics` (admin)
- **Expected:**
  - Both routes accessible
  - No 404 errors
  - Correct view for each role

#### Test 5.4: GeoTruth Integration
- Submit claim with mock location flag
- **Expected:**
  - ML service receives request at `/geotruth/verify`
  - GeoTruth adapter processes claim
  - Multi-modal verification runs
  - Coherence score calculated
  - Decision tier returned

#### Test 5.5: Database Persistence
- Create worker
- Select policy
- File claim
- **Expected:**
  - Worker record in `workers` table
  - Policy record in `policies` table
  - Claim record in `claims` table
  - Fraud decision in `fraud_decisions` table

---

## 🐛 Common Issues & Solutions

### Issue 1: ML Service Not Responding
**Symptom:** Backend gets timeout errors
**Solution:**
```bash
cd ml-services/ML-Service
uvicorn app.main:app --reload --port 8000
```

### Issue 2: GeoTruth Import Error
**Symptom:** `ModuleNotFoundError: No module named 'geotruth'`
**Solution:**
```bash
cd ml-services/ML-Service/Geotruth
pip install -e .
```

### Issue 3: Database Connection Error
**Symptom:** `Can't reach database server`
**Solution:**
```bash
# Check PostgreSQL is running
# Update DATABASE_URL in backend/.env
npx prisma migrate dev
```

### Issue 4: CORS Error
**Symptom:** Frontend can't call backend
**Solution:**
- Verify CORS enabled in backend/server.js
- Check VITE_API_URL in frontend/.env

### Issue 5: Auth Token Invalid
**Symptom:** 401 Unauthorized errors
**Solution:**
- Verify Firebase config in frontend
- Check JWT_SECRET in backend/.env
- Re-login to get fresh token

---

## ✅ Success Criteria

### All Tests Pass When:
- ✅ ML service responds to all endpoints
- ✅ Backend routes return expected data
- ✅ Frontend pages load without errors
- ✅ Currency shows ₹ (not ¥)
- ✅ RiskAnalytics accessible at both routes
- ✅ Analytics calls ML forecast (no self-reference)
- ✅ GeoTruth verification completes
- ✅ Fraud detection returns scores
- ✅ LSTM forecast generates predictions
- ✅ Database operations succeed
- ✅ End-to-end flows complete

---

## 📊 Performance Benchmarks

### Expected Response Times:
- ML fraud detection: < 500ms
- GeoTruth verification: < 800ms
- LSTM forecast: < 1000ms
- Backend API calls: < 200ms
- Frontend page load: < 2s

### Load Testing:
- Concurrent users: 100+
- Claims per minute: 50+
- ML requests per second: 20+

---

## 🎯 Ready for Production When:

1. ✅ All Phase 1-5 tests pass
2. ✅ No console errors in browser
3. ✅ No server errors in logs
4. ✅ Database migrations applied
5. ✅ Environment variables configured
6. ✅ Security measures implemented
7. ✅ Performance benchmarks met
8. ✅ Error handling tested
9. ✅ Edge cases validated
10. ✅ Documentation complete

---

**Current Status:** ✅ ALL INTEGRATIONS COMPLETE - READY FOR TESTING
