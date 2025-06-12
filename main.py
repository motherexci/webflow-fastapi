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

# Amortization schedule (no prints for clean output)
def amortization_schedule(principal,
                          annual_rate,
                          lump_pct,
                          years=20,
                          lump_month=6):
    monthly_rate = annual_rate / 12.0
    total_months = years * 12

    def final_balance(payment):
        bal = principal
        for m in range(1, total_months + 1):
            bal = bal * (1 + monthly_rate) - payment
            if m == lump_month:
                bal -= lump_pct * principal
        return bal

    if monthly_rate == 0:
        hi = principal / total_months
    else:
        hi = principal * (monthly_rate * (1 + monthly_rate)**total_months) \
             / ((1 + monthly_rate)**total_months - 1)
    while final_balance(hi) > 0:
        hi *= 1.5
    lo = 0.0
    p0, p1 = lo, hi
    f0, f1 = final_balance(p0), final_balance(p1)
    for _ in range(80):
        if abs(f1 - f0) < 1e-12:
            break
        p2 = p1 - f1 * (p1 - p0) / (f1 - f0)
        f2 = final_balance(p2)
        p0, f0 = p1, f1
        p1, f1 = p2, f2
        if abs(p1 - p0) < 1e-8:
            break
    return p1

# Reverse calculation: max HELOC from payment budget
def max_heloc_from_budget(monthly_budget,
                          annual_rate,
                          applied_ITC,
                          years=20):
    total_months = years * 12
    lo, hi = 0.0, monthly_budget * total_months
    def f(p): return amortization_schedule(p, annual_rate, applied_ITC, years=years) - monthly_budget
    def df(p, eps=1e-4): return (f(p + eps) - f(p - eps)) / (2*eps)
    principal = hi
    for _ in range(20):
        fp = f(principal)
        dfp = df(principal)
        if abs(dfp) < 1e-8:
            dfp = 1e-8
        principal -= fp / dfp
        if abs(fp) < 1e-6:
            break
    return principal

@app.get("/heloc_option3")
def heloc_option3(
    use_range: bool = Query(False, description="true to use bottom range, false to use top slider"),
    sliderVal: float = Query(0.0, description="Single slider value"),
    lower: float = Query(0.0, description="Lower bound if using range"),
    upper: float = Query(0.0, description="Upper bound if using range"),
):
    """Return structured data for Option 3: instant equity, 30-year savings, HELOC payments, and panel sizes."""
    # Determine input payment
    payment = sliderVal if not use_range else (0.25 * lower + 0.75 * upper)

    # Compute HELOC principal (equity)
    equity = max_heloc_from_budget(
        monthly_budget=payment,
        annual_rate=0.07,
        applied_ITC=0.0,
        years=30
    )
    # HELOC payments with full and half ITC
    payment_full_itc = amortization_schedule(equity, 0.07, 0.30, years=30)
    payment_half_itc = amortization_schedule(equity, 0.07, 0.15, years=30)
    # Panel sizes: 1 kW per $3,000 approx
    base_system_kw = equity / 3.0
    full_itc_kw = (equity * 1.30) / 3.0  # using full 30% ITC to buy panels
    half_itc_kw = (equity * 1.15) / 3.0  # using half 15% ITC to buy panels

    # 30-year savings
    lifetime_savings = payment * 12 * 30  # monthly payment * 12 months * 30 years

    return {
        "instant_equity": f"💰 Instant Equity: Be ${equity:,.2f} richer today.",
        "lifetime_savings": f"⏳ 30-Year Savings: Save ${lifetime_savings:,.2f} by using solar.",
        "heloc_full_itc": f"🔑 Full 30% ITC HELOC Payment: ${payment_full_itc:,.2f}/mo, Panels: {full_itc_kw:,.2f} kW",  
        "heloc_half_itc": f"🔑 Half 15% ITC HELOC Payment: ${payment_half_itc:,.2f}/mo, Panels: {half_itc_kw:,.2f} kW",  
        "base_panels": f"🔋 Base Panel Size: {base_system_kw:,.2f} kW"
    }
