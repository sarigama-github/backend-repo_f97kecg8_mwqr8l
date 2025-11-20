import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Certification Consulting API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str  # 'user' | 'assistant' | 'system'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    reply: str
    suggested_follow_ups: List[str] = []

@app.get("/")
def read_root():
    return {"message": "Certification Consulting Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Simple rule-based consultant for certifications
CERT_TOPICS = {
    "iso 9001": {
        "title": "ISO 9001 (Quality Management)",
        "overview": "Framework for consistent quality, customer satisfaction, and continual improvement.",
        "steps": [
            "Gap analysis against ISO 9001:2015 requirements",
            "Define scope and process mapping",
            "Build QMS documentation and controls",
            "Train teams and run internal audits",
            "Management review and certification audit support"
        ],
        "timeline": "8–16 weeks for most SMEs",
        "benefits": ["Reduced defects", "Higher customer trust", "Operational consistency"],
    },
    "iso 27001": {
        "title": "ISO/IEC 27001 (Information Security)",
        "overview": "ISMS to manage risk, controls (Annex A), and continuous improvement.",
        "steps": [
            "Risk assessment and Statement of Applicability",
            "Policies, procedures, and control implementation",
            "Security awareness and incident response",
            "Internal audit and readiness assessment",
            "Stage 1 & 2 certification audit support"
        ],
        "timeline": "10–20 weeks depending on scope",
        "benefits": ["Reduced security risk", "Stakeholder assurance", "Compliance readiness"],
    },
    "iso 14001": {
        "title": "ISO 14001 (Environmental Management)",
        "overview": "EMS to manage environmental responsibilities systematically.",
        "steps": [
            "Identify aspects and impacts",
            "Set objectives and operational controls",
            "Training and awareness",
            "Internal audit and management review",
            "Certification audit support"
        ],
        "timeline": "8–14 weeks",
        "benefits": ["Reduced environmental impact", "Regulatory compliance", "Cost savings"],
    },
}

GENERIC_SUGGESTIONS = [
    "What standards are most relevant for our industry?",
    "Can you provide a sample project plan?",
    "What documentation do we need to prepare?",
]

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    text = (req.message or "").strip().lower()
    if not text:
        raise HTTPException(status_code=400, detail="Message is required")

    # Basic intent detection
    if any(k in text for k in ["hello", "hi", "hey"]):
        return ChatResponse(
            reply=(
                "Hi! I’m your certification assistant. I can help with ISO 9001, ISO 27001, ISO 14001 and more. "
                "Tell me your goals, industry, and timeframe, and I’ll recommend a path to certification."
            ),
            suggested_follow_ups=GENERIC_SUGGESTIONS,
        )

    for key, info in CERT_TOPICS.items():
        if key in text:
            reply = (
                f"{info['title']}\n\n"
                f"Overview: {info['overview']}\n\n"
                f"Typical steps:\n- " + "\n- ".join(info['steps']) + "\n\n"
                f"Typical timeline: {info['timeline']}\n"
                f"Benefits: " + ", ".join(info['benefits'])
            )
            suggestions = [
                "Can you estimate effort for our team size?",
                "What evidence do auditors expect?",
                "Can we combine multiple standards into an integrated management system?",
            ]
            return ChatResponse(reply=reply, suggested_follow_ups=suggestions)

    if "timeline" in text or "how long" in text:
        return ChatResponse(
            reply=(
                "Timelines vary by scope and readiness. Most clients complete core work in 8–20 weeks. "
                "Share your headcount, sites, and current policies for a tailored plan."
            ),
            suggested_follow_ups=["We have 2 sites and 80 staff—what’s a realistic plan?"],
        )

    if "cost" in text or "price" in text or "budget" in text:
        return ChatResponse(
            reply=(
                "Consulting effort depends on scope and existing maturity. We typically work on fixed-fee phases "
                "aligned to milestones. Share your standards of interest and timeline and we’ll propose options."
            ),
            suggested_follow_ups=["We’re targeting ISO 27001 in Q2—please outline a proposal."],
        )

    # Default response
    return ChatResponse(
        reply=(
            "I can help map the right certification path for you. Which standards are you considering (e.g., ISO 9001, ISO 27001)? "
            "Tell me your industry and timeframe for a tailored plan."
        ),
        suggested_follow_ups=GENERIC_SUGGESTIONS,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
