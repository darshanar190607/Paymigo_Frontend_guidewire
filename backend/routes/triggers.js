import express from 'express';
import axios from 'axios';
import prisma from '../lib/prisma.js';

const router = express.Router();

const ZONE_COORDS = {
  'coimbatore_(zone_1)': { lat: 11.0168, lon: 76.9558 },
  'chennai_(zone_4)': { lat: 13.0827, lon: 80.2707 },
  'bangalore_east': { lat: 12.9716, lon: 77.5946 },
  'mumbai_west': { lat: 19.0760, lon: 72.8777 },
  'default': { lat: 12.9716, lon: 77.5946 }
};

const OPENWEATHER_API_KEY = process.env.OPENWEATHER_API_KEY || '';

router.get('/', async (req, res) => {
  try {
    // We try to find the last active worker to determine the zone
    const worker = await prisma.worker.findFirst({
      orderBy: { id: 'desc' }
    });

    const zoneId = worker?.zoneId || 'default';
    const coords = ZONE_COORDS[zoneId] || ZONE_COORDS['default'];

    let precipitation = 0;
    let windSpeed = 0;
    let waterLogging = 0;

    const { mode } = req.query;

    if (mode === 'flood') {
      precipitation = 120.5;
      windSpeed = 35.0;
      waterLogging = 45.0;
    } else if (mode === 'extreme_wind') {
      precipitation = 2.0;
      windSpeed = 85.0;
      waterLogging = 0.5;
    } else if (mode === 'normal') {
      precipitation = 0.0;
      windSpeed = 12.0;
      waterLogging = 0.0;
    } else if (mode === 'fraud') {
      // Simulate a worker claiming high rainfall while actual data is low
      // This represents GPS spoofing / false claim scenario
      precipitation = 2.0;   // Actual rainfall is LOW — no real event
      windSpeed = 8.0;
      waterLogging = 1.0;
    } else {
      // Fetch real weather from OpenWeatherMap
      const weatherRes = await axios.get(
        `https://api.openweathermap.org/data/2.5/weather?lat=${coords.lat}&lon=${coords.lon}&appid=${OPENWEATHER_API_KEY}&units=metric`
      );

      const current = weatherRes.data;
      precipitation = current.rain ? (current.rain['1h'] || 0) : 0;
      windSpeed = (current.wind?.speed || 0) * 3.6; // convert m/s to km/h
      waterLogging = precipitation > 10 ? (precipitation * 0.8) : (precipitation * 0.2);
    }

    // Determine status
    let status = 'MONITORING';
    const rainfallThreshold = 15.0; // mm
    const windThreshold = 45.0; // km/h

    if (mode === 'fraud') {
      // Fraud mode: ML detected anomaly — block ALL payouts regardless of readings
      status = 'FRAUD_DETECTED';
    } else if (precipitation >= rainfallThreshold || windSpeed >= windThreshold) {
      status = 'PAYOUT_TRIGGERED';
    } else if (precipitation > 5.0 || windSpeed > 30.0) {
      status = 'WARNING';
    }

    res.json({
      rainfall: parseFloat(precipitation.toFixed(1)),
      windSpeed: parseFloat(windSpeed.toFixed(1)),
      waterLogging: parseFloat(waterLogging.toFixed(1)),
      status,
      thresholds: {
        rainfall: rainfallThreshold,
        wind: windThreshold
      },
      zone: zoneId,
      lastUpdated: new Date().toISOString()
    });

  } catch (error) {
    console.error('Weather API error:', error.message);
    res.json({
      rainfall: 14.2,
      windSpeed: 22.5,
      waterLogging: 4.5,
      status: 'MONITORING',
      error: 'Using fallback data'
    });
  }
});

export default router;
