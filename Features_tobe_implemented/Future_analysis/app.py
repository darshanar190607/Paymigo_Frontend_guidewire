from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
import os
import sys
import random
import uvicorn

# Add the model directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'risk_forecaster', 'risk_forecaster'))
from predict import predict_disruption

app = FastAPI(title="RiskOps ML Bridge")

# Serve static files (if you have CSS/JS in separate files later)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Climate Scenarios
def get_latest_weather_history(scenario="nominal"):
    history = []
    for _ in range(14):
        # Base values
        rain = random.uniform(0, 2)
        temp = random.uniform(20, 28)
        storm = 0
        flood = 0
        
        if scenario == "storm":
            rain = random.uniform(20, 55)
            temp = random.uniform(15, 20)
            storm = 1 if random.random() > 0.3 else 0
        elif scenario == "flood":
            rain = random.uniform(5, 15)
            flood = 1
            
        history.append({
            'rain_mm': rain,
            'temp_c': temp,
            'humidity_pct': random.uniform(60, 90) if scenario != "nominal" else random.uniform(40, 60),
            'wind_speed_kmph': random.uniform(30, 80) if scenario == "storm" else random.uniform(5, 15),
            'pressure_hpa': random.uniform(980, 1000) if scenario == "storm" else random.uniform(1010, 1015),
            'storm_alert_flag': storm,
            'flood_alert_flag': flood,
            'heatwave_flag': 0,
            'high_wind_flag': 1 if scenario == "storm" else 0,
            'rain_3day_avg': 2.5 if scenario == "nominal" else 35.0,
            'rain_7day_avg': 1.8 if scenario == "nominal" else 20.0
        })
    return history

@app.get("/")
async def read_index():
    return FileResponse('pay.html')

@app.get("/api/forecast")
async def get_forecast(scenario: str = "nominal", zone_id: int = 0):
    try:
        # Vary the input history slightly based on zone to create different visual signatures
        history = get_latest_weather_history(scenario)
        
        # Modify zones to have vastly different risk signatures for clear visual feedback
        if zone_id == 0:
            for h in history: h['wind_speed_kmph'] *= 2.5  # Windy Harbor
        elif zone_id == 1:
            for h in history: h['rain_mm'] *= 4.0          # Floody Coastal
        else:
            for h in history: h['temp_c'] += 10.0          # Hot Central
            
        result = predict_disruption(history)
        
        max_prob = max(result["disruption_probability"])
        expected_claims = int(800 + (max_prob * 1500))
        exposed_capital = round(30.5 + (max_prob * 25.0), 1)
        
        next_day_prob = result["disruption_probability"][0]
        hourly_probs = [
            round(next_day_prob * (0.8 + random.uniform(0, 0.4)), 4) 
            for _ in range(24)
        ]
        
        return {
            "status": "success",
            "data": {
                **result,
                "hourly_probability": hourly_probs,
                "expected_claims": expected_claims,
                "exposed_capital": exposed_capital,
                "active_scenario": scenario,
                "active_zone": zone_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI_Risk_Chat_agent Configuration
RISK_AGENT_KEY = "REDACTED"
RISK_AGENT_URL = "https://api.groq.com/openai/v1/chat/completions" # Abstraction endpoint

@app.get("/api/chat")
async def chat_with_agent(message: str, current_zone: str = "Unknown", risk_prob: float = 0.0):
    try:
        system_prompt = f"""
        You are the PAYMIGO AI Risk Assistant (AI_Risk_Chat_agent).
        You analyze parametric insurance risks using live LSTM model data.
        Current Context:
        - Active Zone: {current_zone}
        - LSTM Disruption Probability: {risk_prob:.2%}
        - System Status: Stable
        
        Provide professional, concise, and expert advice for RiskOps administrators.
        If probabilities are high, suggest risk mitigation or liquidity adjustments.
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RISK_AGENT_URL,
                headers={
                    "Authorization": f"Bearer {RISK_AGENT_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 300
                },
                timeout=20.0
            )
            
            data = response.json()
            return {"reply": data['choices'][0]['message']['content']}
            
    except Exception as e:
        return {"reply": f"AI_Risk_Chat_agent is currently optimizing its pathways. (Error: {str(e)})"}

if __name__ == "__main__":
    print("FastAPI RiskOps Server starting at http://127.0.0.1:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
