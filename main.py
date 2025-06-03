# main.py

from fastapi import FastAPI, HTTPException, Query
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

# ── /compute ENDPOINT: 
#    • use_range: "true" or "false"
#    • sliderVal: float (ignored if use_range is true)
#    • lower: float  (ignored if use_range is false)
#    • upper: float  (ignored if use_range is false)
@app.get("/compute")
def compute_value(
    use_range: bool = Query(False, description="true to use the bottom range, false to use the top slider"),
    sliderVal: float = Query(0.0, description="Single slider value"),
    lower: float = Query(0.0, description="Lower bound if using range"),
    upper: float = Query(0.0, description="Upper bound if using range"),
):
    try:
        if use_range:
            # Weighted average: 25% * lower + 75% * upper
            weighted_avg = 0.25 * lower + 0.75 * upper
            return {"result": weighted_avg * 2}
        else:
            # Just double the single slider value
            return {"result": sliderVal * 2}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))