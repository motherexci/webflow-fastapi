# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ── CORS SETUP: allow only your Webflow domain to call this API
origins = ["https://solar-1e6d6b.webflow.io"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── /double ENDPOINT: takes sliderVal (float) → returns { "result": sliderVal * 2 }
@app.get("/double")
def double_number(sliderVal: float):
    try:
        return { "result": sliderVal * 2 }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
