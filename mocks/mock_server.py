"""Mock server for all external APIs: email/phone validation, Google/Meta Ads, OAuth flows."""
import random
import uuid
from datetime import date, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="EPI Mock Services")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Email Validation ---
class EmailValidationRequest(BaseModel):
    email: str


@app.post("/validate/email")
async def validate_email(req: EmailValidationRequest):
    email = req.email.lower()
    if "invalid" in email or email.endswith(".xyz"):
        return {"email": email, "result": "invalid"}
    if "disposable" in email or email.endswith("@mailinator.com"):
        return {"email": email, "result": "disposable"}
    if "catchall" in email:
        return {"email": email, "result": "catch_all"}
    return {"email": email, "result": "valid"}


# --- Phone Validation ---
class PhoneValidationRequest(BaseModel):
    phone: str


@app.post("/validate/phone")
async def validate_phone(req: PhoneValidationRequest):
    phone = req.phone.strip()
    if phone.startswith("+1800"):
        return {"phone": phone, "result": "voip"}
    if phone.startswith("+1900"):
        return {"phone": phone, "result": "invalid"}
    if phone.startswith("+1"):
        return {"phone": phone, "result": "mobile"}
    if phone.startswith("+44"):
        return {"phone": phone, "result": "landline"}
    return {"phone": phone, "result": "valid"}


# --- Google Ads Mock ---
@app.get("/google-ads/conversions")
async def google_ads_conversions(
    customer_id: str = Query(...),
    date: str = Query(...),
):
    campaigns = [
        {"campaign_id": "gc_001", "campaign_name": "Brand Search", "ad_group_id": "ag_001", "ad_group_name": "Brand Terms"},
        {"campaign_id": "gc_002", "campaign_name": "Lead Gen", "ad_group_id": "ag_002", "ad_group_name": "Contact Forms"},
        {"campaign_id": "gc_003", "campaign_name": "Retargeting", "ad_group_id": "ag_003", "ad_group_name": "Site Visitors"},
    ]
    data = []
    for c in campaigns:
        data.append({
            **c,
            "conversion_action": "form_submit",
            "conversions": random.randint(5, 25),
            "clicks": random.randint(50, 200),
            "impressions": random.randint(1000, 5000),
            "spend": round(random.uniform(50, 300), 2),
        })
    return {"data": data, "customer_id": customer_id, "date": date}


# --- Meta Ads Mock ---
@app.get("/meta-ads/conversions")
async def meta_ads_conversions(
    account_id: str = Query(...),
    date: str = Query(...),
):
    campaigns = [
        {"campaign_id": "mc_001", "campaign_name": "FB Lead Ads", "adset_id": "as_001", "adset_name": "Lookalike"},
        {"campaign_id": "mc_002", "campaign_name": "IG Stories", "adset_id": "as_002", "adset_name": "Interest"},
    ]
    data = []
    for c in campaigns:
        data.append({
            **c,
            "action_type": "lead",
            "conversions": random.randint(3, 15),
            "clicks": random.randint(30, 150),
            "impressions": random.randint(2000, 10000),
            "spend": round(random.uniform(30, 200), 2),
        })
    return {"data": data, "account_id": account_id, "date": date}


# --- OAuth Mocks ---
@app.get("/oauth/google/authorize")
async def google_oauth_authorize(
    client_id: str = Query(""),
    redirect_uri: str = Query(""),
    state: str = Query(""),
):
    return {
        "redirect_url": f"{redirect_uri}?code=mock_google_auth_code_{uuid.uuid4().hex[:8]}&state={state}"
    }


@app.post("/oauth/google/token")
async def google_oauth_token():
    return {
        "access_token": f"mock_google_access_{uuid.uuid4().hex[:16]}",
        "refresh_token": f"mock_google_refresh_{uuid.uuid4().hex[:16]}",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


@app.get("/oauth/meta/authorize")
async def meta_oauth_authorize(
    client_id: str = Query(""),
    redirect_uri: str = Query(""),
    state: str = Query(""),
):
    return {
        "redirect_url": f"{redirect_uri}?code=mock_meta_auth_code_{uuid.uuid4().hex[:8]}&state={state}"
    }


@app.post("/oauth/meta/token")
async def meta_oauth_token():
    return {
        "access_token": f"mock_meta_access_{uuid.uuid4().hex[:16]}",
        "token_type": "Bearer",
        "expires_in": 5184000,
    }


# --- Slack OAuth Mock ---
@app.post("/oauth/slack/token")
async def slack_oauth_token():
    return {
        "ok": True,
        "access_token": f"xoxb-mock-{uuid.uuid4().hex[:16]}",
        "team": {"id": "T_MOCK_001", "name": "Mock Workspace"},
        "bot_user_id": "U_MOCK_BOT",
    }


@app.get("/health")
async def mock_health():
    return {"status": "healthy", "service": "epi-mocks"}
