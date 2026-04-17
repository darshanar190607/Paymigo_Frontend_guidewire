import express from 'express';
import { PrismaClient } from '@prisma/client';
const router = express.Router();
const prisma = new PrismaClient();

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8000';

// City to zone mapping - this should match your existing zones
const CITY_ZONE_MAP = {
  'chennai': 'chennai-central',
  'mumbai': 'mumbai-western',
  'delhi': 'delhi-ncr',
  'bangalore': 'bangalore-electronic-city',
  'hyderabad': 'hyderabad-hitech-city',
  'kolkata': 'kolkata-salt-lake',
  'pune': 'pune-hinjewadi',
  'ahmedabad': 'ahmedabad-gandhinagar',
  'jaipur': 'jaipur-mansarovar',
  'lucknow': 'lucknow-gomti-nagar'
};

// Extract city from headline text
function extractCityFromHeadline(text) {
  const cities = Object.keys(CITY_ZONE_MAP);
  const lowerText = text.toLowerCase();
  
  for (const city of cities) {
    if (lowerText.includes(city)) {
      return city;
    }
  }
  return null;
}

// POST /nlp/process-headlines - Process headlines from ML service
router.post('/process-headlines', async (req, res) => {
  try {
    const { headlines } = req.body;
    
    if (!headlines || !Array.isArray(headlines)) {
      return res.status(400).json({ error: 'Headlines array is required' });
    }

    const processedEvents = [];
    
    for (const headline of headlines) {
      const city = extractCityFromHeadline(headline.text);
      const zone = city ? CITY_ZONE_MAP[city] : 'unknown';
      
      // Only store events with confidence > 0.7 and not 'normal'
      if (headline.confidence > 0.7 && headline.label !== 'normal') {
        const nlpEvent = await prisma.nLPEvent.create({
          data: {
            text: headline.text,
            label: headline.label,
            confidence: headline.confidence,
            source: headline.source || 'ml-service',
            zone: zone
          }
        });
        
        processedEvents.push(nlpEvent);
      }
    }
    
    res.json({
      success: true,
      processed: processedEvents.length,
      events: processedEvents
    });
    
  } catch (error) {
    console.error('Error processing headlines:', error);
    res.status(500).json({ error: 'Failed to process headlines' });
  }
});

// POST /nlp/fetch-and-process - Backend proxy: fetches headlines from ML service, then processes them
// This avoids CORS issues when calling the ML service directly from the browser.
router.post('/fetch-and-process', async (req, res) => {
  try {
    // Call the ML service from the backend (no CORS)
    const mlRes = await fetch(`${ML_SERVICE_URL}/curfew/simulate-news`);
    if (!mlRes.ok) {
      return res.status(502).json({ error: `ML service returned ${mlRes.status}. Make sure uvicorn is running on port 8000.` });
    }
    const mlData = await mlRes.json();
    const headlines = mlData.headlines || [];

    // Process through our existing logic
    const processedEvents = [];
    for (const headline of headlines) {
      const city = extractCityFromHeadline(headline.text);
      const zone = city ? CITY_ZONE_MAP[city] : 'unknown';
      if (headline.confidence > 0.7 && headline.label !== 'normal') {
        const nlpEvent = await prisma.nLPEvent.create({
          data: {
            text: headline.text,
            label: headline.label,
            confidence: headline.confidence,
            source: headline.source || 'ml-service',
            zone: zone
          }
        });
        processedEvents.push(nlpEvent);
      }
    }

    res.json({ success: true, processed: processedEvents.length, events: processedEvents });
  } catch (error) {
    console.error('Error in fetch-and-process:', error);
    res.status(500).json({ error: 'Failed to reach ML service. Is uvicorn running on port 8000?' });
  }
});

// GET /nlp/alerts - Fetch all active NLP events
router.get('/alerts', async (req, res) => {
  try {
    const { status = 'active', zone } = req.query;
    
    const whereClause = {
      status: status
    };
    
    if (zone && zone !== 'all') {
      whereClause.zone = zone;
    }
    
    const alerts = await prisma.nLPEvent.findMany({
      where: whereClause,
      orderBy: {
        createdAt: 'desc'
      },
      take: 50 // Limit to last 50 alerts
    });
    
    res.json(alerts);
    
  } catch (error) {
    console.error('Error fetching alerts:', error);
    res.status(500).json({ error: 'Failed to fetch alerts' });
  }
});

// POST /nlp/convert-to-trigger - Convert NLP alert to system trigger
router.post('/convert-to-trigger', async (req, res) => {
  try {
    const { nlpEventId, threshold = 0.8 } = req.body;
    
    if (!nlpEventId) {
      return res.status(400).json({ error: 'NLP Event ID is required' });
    }
    
    // Get the NLP event
    const nlpEvent = await prisma.nLPEvent.findUnique({
      where: { id: nlpEventId }
    });
    
    if (!nlpEvent) {
      return res.status(404).json({ error: 'NLP Event not found' });
    }
    
    if (nlpEvent.status !== 'active') {
      return res.status(400).json({ error: 'NLP Event is not active' });
    }
    
    if (nlpEvent.confidence < threshold) {
      return res.status(400).json({ error: 'Confidence threshold not met' });
    }
    
    // Find zone by name
    const zone = await prisma.zone.findFirst({
      where: {
        OR: [
          { name: { contains: nlpEvent.zone, mode: 'insensitive' } },
          { city: { contains: nlpEvent.zone, mode: 'insensitive' } }
        ]
      }
    });
    
    if (!zone) {
      return res.status(404).json({ error: 'Zone not found for this event' });
    }
    
    // Create trigger event
    const triggerEvent = await prisma.triggerEvent.create({
      data: {
        zoneId: zone.id,
        triggerType: `nlp-${nlpEvent.label}`,
        actualValue: nlpEvent.confidence,
        threshold: threshold,
        confidence: nlpEvent.confidence,
        isActive: true,
        fallbackUsed: false
      }
    });
    
    // Update NLP event status
    await prisma.nLPEvent.update({
      where: { id: nlpEventId },
      data: { status: 'triggered' }
    });
    
    res.json({
      success: true,
      triggerEvent,
      nlpEvent: { ...nlpEvent, status: 'triggered' }
    });
    
  } catch (error) {
    console.error('Error converting to trigger:', error);
    res.status(500).json({ error: 'Failed to convert to trigger' });
  }
});

// POST /nlp/ignore-alert - Mark NLP alert as ignored
router.post('/ignore-alert', async (req, res) => {
  try {
    const { nlpEventId } = req.body;
    
    if (!nlpEventId) {
      return res.status(400).json({ error: 'NLP Event ID is required' });
    }
    
    const updatedEvent = await prisma.nLPEvent.update({
      where: { id: nlpEventId },
      data: { status: 'ignored' }
    });
    
    res.json({
      success: true,
      event: updatedEvent
    });
    
  } catch (error) {
    console.error('Error ignoring alert:', error);
    res.status(500).json({ error: 'Failed to ignore alert' });
  }
});

// GET /nlp/stats - Get NLP statistics
router.get('/stats', async (req, res) => {
  try {
    const stats = await prisma.nLPEvent.groupBy({
      by: ['label', 'status'],
      _count: {
        id: true
      }
    });
    
    const totalEvents = await prisma.nLPEvent.count();
    const activeEvents = await prisma.nLPEvent.count({
      where: { status: 'active' }
    });
    
    res.json({
      total: totalEvents,
      active: activeEvents,
      breakdown: stats
    });
    
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

// DELETE /nlp/clear-old - Clear old NLP events (older than 7 days)
router.delete('/clear-old', async (req, res) => {
  try {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    const result = await prisma.nLPEvent.deleteMany({
      where: {
        createdAt: {
          lt: sevenDaysAgo
        },
        status: {
          in: ['ignored', 'triggered']
        }
      }
    });
    
    res.json({
      success: true,
      deleted: result.count
    });
    
  } catch (error) {
    console.error('Error clearing old events:', error);
    res.status(500).json({ error: 'Failed to clear old events' });
  }
});

export default router;
