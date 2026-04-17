import fs from 'fs';
import path from 'path';
import csvParser from 'csv-parser';

// The path to the CSV file outputted by the ML service
const CSV_FILE_PATH = path.resolve('C:\\Guidewire_Devtrails\\PayMigo_Final\\ml-services\\ML-Service\\zone_clustered_output.csv');

/**
 * Reads the clustered zone output and returns a dictionary indexed by zone id/name
 */
export async function getZoneData() {
  return new Promise((resolve, reject) => {
    const results = {};
    if (!fs.existsSync(CSV_FILE_PATH)) {
      console.warn(`CSV file not found at ${CSV_FILE_PATH}, falling back to default stats.`);
      return resolve({});
    }

    fs.createReadStream(CSV_FILE_PATH)
      .pipe(csvParser())
      .on('data', (data) => {
        // e.g. "pincode","city","avg_rainfall","heavy_rain_days","avg_wind_speed","avg_pressure","storm_days","avg_aqi"
        if (data.city) {
          results[data.city.toLowerCase().replace(/ /g, '_')] = data;
        }
      })
      .on('end', () => {
        resolve(results);
      })
      .on('error', (err) => {
        console.error('Error parsing zone CSV:', err);
        resolve({});
      });
  });
}

/**
 * Helper to extract features required for the Python ML service given a zone Id.
 */
export async function getZoneFeatures(zoneId) {
  const dictionary = await getZoneData();
  const zoneStats = dictionary[zoneId] || null;

  if (zoneStats) {
    return {
      storm_days: parseFloat(zoneStats.storm_days || 0),
      heavy_rain_days: parseFloat(zoneStats.heavy_rain_days || 0),
      avg_aqi: parseFloat(zoneStats.avg_aqi || 100),
      zone_risk_tier: zoneStats.zone_risk_tier ? parseFloat(zoneStats.zone_risk_tier) : null
    };
  }

  // Fallback default values
  return {
    storm_days: 0,
    heavy_rain_days: 0,
    avg_aqi: 100,
    zone_risk_tier: null
  };
}
