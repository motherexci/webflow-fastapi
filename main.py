from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["https://solar-1e6d6b.webflow.io"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["*"])

@app.get("/compute")
def compute_value(
    use_range: bool = Query(False),
    sliderVal: float = Query(0.0),
    lower: float = Query(0.0),
    upper: float = Query(0.0),
):
    try:
        if use_range:
            weighted = 0.25*lower + 0.75*upper
            return {"result": weighted * 3}
        else:
            return {"result": sliderVal * 3}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))