# FinMatch AI: AI-Powered Personalized Credit Card & Loan Recommendation Platform

FinMatch AI is a full-stack financial technology application tailored for the Indian financial market. It eliminates tedious 30–50 field questionnaires. Users describe their circumstances, financial preferences, and goals in plain natural language. An LLM parses and structures their requirements, while **strictly deterministic, explainable algorithms** make eligibility and ranking calculations.

Every product recommendation is backed by real, field-level evidence scraped and verified from official bank portals (HDFC Bank, State Bank of India, ICICI Bank, Axis Bank), complete with transparent calculation breakdowns (standard amortized EMI for loans, net reward benefit with spending category caps and fee waivers for cards).

---

## 🌟 Key Features

1. **Conversational Financial Profiler**:
   - Describe monthly income, employer, credit score, spending patterns, or borrowing needs in one paragraph or incremental messages.
   - Robust Indian currency, LPA, Lakhs, k, and CIBIL score normalization with field provenance tracking (`user_provided`, `ai_inferred`, `confirmed`).
2. **Adaptive Clarification Engine**:
   - Asks at most 2–3 targeted, high-materiality questions with selectable quick option chips instead of rendering lengthy forms.
3. **Deterministic Financial Math**:
   - **Loan EMI & Amortisation**: Fully amortizing standard formula $EMI = P \times r \times \frac{(1+r)^n}{(1+r)^n - 1}$ with zero-interest handling, total scheduled interest, processing fee caps, 18% GST, and debt-to-income (FOIR) calculations.
   - **Credit Card Net Benefit**: Spend distribution across categories (groceries, online shopping, travel, dining, fuel, utilities), monthly reward caps, fee waiver thresholds, and first-year net benefit accounting for welcome bonuses.
4. **Independent Evidence & Verification Engine**:
   - 10 automated integrity checks: schema validation, numeric bounds, currency checks, cross-field consistency, evidence-to-value matching, official domain whitelisting, freshness checks, and discrepancy flagging.
   - Status tracking per field and product: `verified`, `partially_verified`, `conflicting_sources`, `stale`, `unverified`.
5. **Grounded LLM Explainer ("Why This Matches You")**:
   - Generates personalized reasoning citing user goals, matched priorities, trade-offs, and official source links without hallucinating numbers.
6. **Side-by-Side Product Comparison**:
   - Compare up to 4 credit cards or loans across fees, waivers, reward caps, net annual benefits, EMI ranges, and pros/cons.
7. **Ingestion & Admin Dashboard**:
   - Monitor crawled bank portals, inspection status, field-level discrepancies, and trigger re-crawls.
8. **Mock & Multi-Provider AI**:
   - Works 100% offline in Mock Mode with zero external API key requirements.
   - Also supports Google Gemini, OpenAI, or Anthropic via standard environment configuration.

---

## 📐 Architecture & Pipeline

```
User Natural Language Input
       │
       ▼
[Stage 1: Profile Understanding Agent] (services/profile_parser.py)
       │
       ▼
[Stage 2: Adaptive Clarification Engine] (services/profile_clarifier.py)
       │
       ├──► [Stages 3-5: Official Bank Discovery, Fetcher & Verifier]
       │       └── Official sources: HDFC Bank, SBI Card / SBI, ICICI Bank
       │       └── Grounded evidence excerpts, domain whitelist, SSRF guard
       │
       ▼
[Stage 6: Eligibility Engine] (services/eligibility_engine.py)
       └── meets_published_criteria | may_meet_criteria | does_not_meet_published_criteria
       │
       ▼
[Stage 7: Deterministic Matching & Ranking Engine] (services/matching_engine.py)
       └── 6 Dimensions: Eligibility (30%), Financial Fit (25%), Preferences (20%),
           Cost Efficiency (15%), Reliability (5%), Freshness (5%)
       └── Stable tie-breaking rules
       │
       ▼
[Stage 8: LLM Explainer] (services/recommendation_explainer.py)
       └── Why it matches, trade-offs, assumptions, official links
       │
       ▼
[Stage 9: React + TypeScript UI] (frontend/)
```

---

## 🚀 Quickstart Guide

### One-Command Quickstart
Run both the backend and frontend simultaneously:
```bash
./start.sh
```

- **Frontend Application**: `http://localhost:5173`
- **FastAPI Documentation**: `http://localhost:8000/docs`
- **Backend Health Check**: `http://localhost:8000/api/v1/health`

---

### Running Services Separately

#### 1. Backend Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend

# If using the local standalone Node:
export PATH="$PWD/../.tools/node/bin:$PATH"

# Install dependencies & start dev server
npm install
npm run dev
```

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
source .venv/bin/activate
pytest backend/tests -v
```

All 29 tests cover:
- Natural-language profile parsing with Indian units & abbreviations (Lakh, k, LPA, CIBIL)
- Profile updates, corrections, and priority persistence
- Adaptive clarification question generation
- Safe website fetching, timeout handling, and SSRF prevention
- Clean HTML extraction and table parsing
- Evidence grounding and independent verification checks
- Consistency violations and stale data detection
- Deterministic credit card reward calculation, spending caps, and fee waivers
- Amortizing loan EMI calculation, rate ranges, and zero-interest handling
- End-to-end API workflows (profile creation, recommendation generation, product comparison, and ingestion monitoring)

---

## 🛡️ Security & Responsible Financial Guidance

- **SSRF Prevention**: All outbound fetching restricts target URLs to whitelisted bank domains and blocks loopback, private RFC-1918, link-local, and cloud metadata addresses.
- **Privacy First**: We do not collect banking passwords, OTPs, or full card numbers.
- **Informational Disclaimer**: Recommendations are algorithmic and informational. Final approval, offered interest rates, and product terms are determined by the respective financial institutions under RBI underwriting guidelines.
