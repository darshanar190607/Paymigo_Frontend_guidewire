import axios from 'axios';

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8000';

export const mlClient = axios.create({
  baseURL: ML_SERVICE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const calculatePremium = async (workerData: any) => {
  try {
    const response = await mlClient.post('/premium/calculate', workerData);
    return response.data;
  } catch (error) {
    console.error('Error calculating premium:', error);
    return { premium: 112 }; // Fallback
  }
};

export const checkFraud = async (claimData: any) => {
  try {
    const response = await mlClient.post('/fraud/check', claimData);
    return response.data;
  } catch (error) {
    console.error('Error checking fraud:', error);
    return { is_fraud: false, confidence: 0.99 }; // Fallback
  }
};
