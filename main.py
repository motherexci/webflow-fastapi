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

# same amortization function as before, but with deactivated print statements.
def amortization_schedule(principal,
                          annual_rate,
                          lump_pct,
                          years=20,
                          lump_month=6):
    """
    Compute the fixed monthly payment to amortize a loan over `years*12` months,
    with a one-time lump sum at `lump_month` months equal to `lump_pct * principal`.
    Uses the secant method (instead of bisection) to zero out the remaining balance.
    """
    monthly_rate = annual_rate / 12.0
    total_months = years * 12

    def final_balance(payment):
        bal = principal
        for m in range(1, total_months + 1):
            bal = bal * (1 + monthly_rate) - payment
            if m == lump_month:
                bal -= lump_pct * principal
        return bal

    # Upper bound on payment (standard amortization)
    if monthly_rate == 0:
        hi = principal / total_months
    else:
        hi = principal * (monthly_rate * (1 + monthly_rate)**total_months) \
             / ((1 + monthly_rate)**total_months - 1)
    # Ensure hi is high enough so that final_balance(hi) <= 0
    while final_balance(hi) > 0:
        hi *= 1.5
    lo = 0.0

    # Secant method to find payment that zeroes the balance
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

# Reverse Calc: Max HELOC from Monthly Budget
def max_heloc_from_budget(monthly_budget,
                          annual_rate,
                          applied_ITC,
                          years=20):
    """
    Given a fixed monthly payment budget, compute the maximum principal you can borrow (HELOC)
    amortized over 'years' years with a one-time lump sum credit.
    """
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
        principal -= fp/dfp
        if abs(fp) < 1e-6:
            break
    return principal

@app.get("/heloc_message")
def heloc_message(
    use_range: bool = Query(False, description="true to use bottom range, false to use top slider"),
    sliderVal: float = Query(0.0, description="Single slider value"),
    lower: float = Query(0.0, description="Lower bound if using range"),
    upper: float = Query(0.0, description="Upper bound if using range"),
):
    """Return detailed HELOC equity messages based on the user's inputs."""
    # Determine input payment
    if use_range:
        payment = 0.25 * lower + 0.75 * upper
    else:
        payment = sliderVal

    # Compute HELOC principal and related metrics
    equity = max_heloc_from_budget(
        monthly_budget=payment,
        annual_rate=0.07,
        applied_ITC=0.00,
        years=30
    )
    payment_with_itc = amortization_schedule(
        equity,
        annual_rate=0.07,
        lump_pct=0.30,
        lump_month=6,
        years=30
    )
    payment_with_half_itc = amortization_schedule(
        equity,
        annual_rate=0.07,
        lump_pct=0.15,
        lump_month=6,
        years=30
    )
    itc_amount = equity * 0.30
    elec_input = payment  # rename for consistency

    # Construct messages
    msg1 = (
        f"This margin—through this tax incentive—is liquid equity, liquid capital you extracted by using energy "
        f"that's already beaming on your roof instead of paying Duke Energy to burn gas. You can choose to be "
        f"${itc_amount:,.2f} richer right now (the full ITC credit)—since the equity you extracted is less than "
        f"the increase in home value due to the solar panels—plus the literal ITC tax credit, with no change in "
        f"how much you ‘pay for electricity as a whole.’ Or you can choose to be ${(elec_input - payment_with_itc)*30.0*12.0:,.2f} richer over the next 30 years by simply using the panels on your roof instead of buying power."
    )

    msg2 = (
        f"[independent_max_heloc]:  If you apply the full ITC credit to the loan, "
        f"your monthly HELOC payment becomes: ${payment_with_itc:,.2f}. "
        f"If you apply only half the ITC (15%), your monthly payment becomes: "
        f"${payment_with_half_itc:,.2f}, and by allocating the remaining 15% ITC "
        f"toward panels you could install a {((equity * 1.15) / 3.0):,.2f} kW system."
    )

    return {"message1": msg1, "message2": msg2}
