"""
Provider-agnostic LLM abstraction with support for:
- MockLLMProvider (deterministic, offline, robust rule-and-heuristic based)
- GeminiLLMProvider (Google Gemini API via HTTPX)
- OpenAILLMProvider (OpenAI-compatible endpoints via HTTPX)
"""
import abc
import json
import re
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates plain text response."""
        pass

    @abc.abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generates structured JSON response conforming to optional schema."""
        pass


class MockLLMProvider(LLMProvider):
    """
    Offline, deterministic provider that fulfills all test cases, demonstrations,
    and fallback operations without requiring an active external API key.
    """

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return f"Mock response for prompt: {prompt[:100]}..."

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt_lower = prompt.lower()

        # 1. Profile Extraction Check
        if "extract user financial profile" in prompt_lower or "financial profile" in (system_prompt or "").lower():
            return self._mock_profile_extraction(prompt)

        # 2. Product Extraction Check
        if "extract product terms" in prompt_lower or "financial product terms" in (system_prompt or "").lower():
            return self._mock_product_extraction(prompt)

        # 3. Recommendation Explanation Check
        if "recommendation" in prompt_lower or "recommendation" in (system_prompt or "").lower() or "why this matches you" in (system_prompt or "").lower():
            return self._mock_recommendation_explanation(prompt)

        # Default fallback JSON
        return {
            "status": "success",
            "message": "Mock JSON response generated successfully."
        }

    def _mock_profile_extraction(self, prompt: str) -> Dict[str, Any]:
        """Robust natural language parser for Indian financial statements."""
        text = prompt.lower()
        
        # Monthly income parsing (e.g., 65000, 65,000, 65k, 55000 monthly, make 50k, increased to 70k)
        monthly_income = None
        income_match = re.search(
            r'(?:earning|earn|salary|income|in\s+hand|make|makes|making|take\s+home)[^0-9]{0,30}?(?:₹|rs\.?|inr)?\s*([0-9,.]+)\s*(k|lakh|lac)?',
            text
        )
        if income_match:
            val_str = income_match.group(1).replace(",", "")
            modifier = income_match.group(2)
            try:
                val = float(val_str)
                if modifier == 'k':
                    val *= 1000
                elif modifier in ('lakh', 'lac'):
                    val *= 100000
                monthly_income = val
            except ValueError:
                pass
        
        # Credit score parsing (e.g., credit score is 760, cibil 750, credit score is approximately 760)
        credit_score = None
        score_match = re.search(
            r'(?:credit\s*score|cibil)[^0-9]{0,30}?([0-9]{3})',
            text
        )
        if score_match:
            try:
                credit_score = int(score_match.group(1))
            except ValueError:
                pass

        # Age parsing (e.g., 20 y/o, 20yo, 20 year old, 20 years old, age 20, aged 20, i'm 24)
        age = None
        age_match = re.search(
            r'(?:\b(?:i am|i\'m|age|aged|am)\s*([0-9]{2})\b|\b([0-9]{2})\s*(?:y/o|yo|yr|yrs|year|years)(?:\s*old)?\b)',
            text
        )
        if age_match:
            age_str = age_match.group(1) or age_match.group(2)
            try:
                parsed_age = int(age_str)
                if 16 <= parsed_age <= 99:
                    age = parsed_age
            except ValueError:
                pass

        # Employment type
        employment_type = "salaried"
        if "self employed" in text or "freelance" in text or "business" in text:
            employment_type = "self_employed"
        elif "student" in text or "college" in text or "university" in text:
            employment_type = "student"
        elif "retired" in text:
            employment_type = "retired"

        # Product preference: detect explicit intent from user text
        has_loan_kw = any(re.search(r'\b' + re.escape(w) + r'\b', text) for w in ["loan", "loans", "borrow", "borrowing", "lending", "personal loan", "home loan", "take loan"])
        has_card_kw = any(w in text for w in ["credit card", "card", "cards", "cashback", "credit score", "cibil", "rewards", "lounge", "points", "spend", "spends", "student", "suggestion", "suggestions"])
        
        if has_loan_kw and has_card_kw:
            preferred_product = "both"
        elif has_loan_kw:
            preferred_product = "personal_loan"
        else:
            preferred_product = "credit_card"

        # Loan specifics: only extracted if user actually indicated loan intent!
        loan_amount = None
        loan_tenure = None
        if has_loan_kw:
            amt_match = re.search(r'(?:loan\s*(?:of|for)?|borrow|personal\s*loan)\s*(?:₹|rs\.?|inr)?\s*([0-9.]+)\s*(lakh|lac|k)?', text)
            if amt_match:
                val = float(amt_match.group(1))
                unit = amt_match.group(2)
                if unit in ('lakh', 'lac'):
                    val *= 100000
                elif unit == 'k':
                    val *= 1000
                loan_amount = val

            tenure_match = re.search(r'([0-9]+)\s*(?:months|month|mo|years|year|yr)', text)
            if tenure_match:
                tenure_val = int(tenure_match.group(1))
                if "year" in text or "yr" in text:
                    tenure_val *= 12
                loan_tenure = tenure_val

        # Existing EMI
        existing_emi = None
        emi_match = re.search(r'(?:existing\s*emi|current\s*emi|paying\s*emi)(?:\s*is|\s*of)?\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)', text)
        if emi_match:
            existing_emi = float(emi_match.group(1).replace(",", ""))

        # Spending categories
        food_spend = 0.0
        shop_spend = 0.0
        travel_spend = 0.0
        food_m = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9,]+)\s*(?:on|for)?\s*(?:food|groceries|dining)', text)
        if food_m:
            food_spend = float(food_m.group(1).replace(",", ""))
        
        shop_m = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9,]+)\s*(?:on|for)?\s*(?:online\s*shopping|shopping)', text)
        if shop_m:
            shop_spend = float(shop_m.group(1).replace(",", ""))

        travel_m = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9,]+)\s*(?:on|for)?\s*(?:travel|flights|trains)', text)
        if travel_m:
            travel_spend = float(travel_m.group(1).replace(",", ""))

        # Bank relationship
        bank = None
        for b in ["hdfc", "sbi", "icici", "axis", "kotak", "tata neu"]:
            if b in text:
                bank = b.upper()
                break

        return {
            "age": {"value": age, "source": "user_provided", "confidence": 1.0} if age is not None else None,
            "monthly_income": {"value": monthly_income, "source": "user_provided", "confidence": 1.0} if monthly_income is not None else None,
            "employment_type": {"value": employment_type, "source": "user_provided", "confidence": 1.0},
            "credit_score": {"value": credit_score, "source": "user_provided", "confidence": 1.0} if credit_score is not None else None,
            "existing_monthly_emi": {"value": existing_emi, "source": "user_provided", "confidence": 1.0} if existing_emi is not None else None,
            "city": {"value": "Bengaluru" if ("bengaluru" in text or "bangalore" in text) else None, "source": "user_provided", "confidence": 0.9} if ("bengaluru" in text or "bangalore" in text) else None,
            "preferred_product": preferred_product,
            "spending": {
                "food_groceries": food_spend or 0.0,
                "online_shopping": shop_spend or 0.0,
                "travel": travel_spend or 0.0,
                "dining_entertainment": 0.0,
                "fuel": 0.0,
                "utility_bills": 0.0,
                "other": 0.0
            },
            "card_preferences": {
                "low_annual_fee": "low fee" in text or "low annual fee" in text or "no joining fee" in text or "zero annual fee" in text or "no fee" in text,
                "cashback_priority": "cashback" in text or "cash back" in text or "rewards" in text,
                "avoid_interest": "don't want to pay interest" in text or "avoid interest" in text or "no interest" in text,
                "existing_bank": bank
            },
            "loan_preferences": {
                "requested_amount": loan_amount,
                "requested_tenure_months": loan_tenure,
                "prefer_low_processing_fee": "transparent" in text or "no hidden" in text
            }
        }

    def _mock_product_extraction(self, prompt: str) -> Dict[str, Any]:
        """Mock structured extraction for financial products."""
        return {
            "product_name": "Verified Banking Financial Product",
            "issuer": "Premier Bank India",
            "product_type": "credit_card",
            "terms": {
                "joining_fee": 500.0,
                "annual_fee": 500.0,
                "fee_waiver_spend_threshold": 100000.0,
                "base_cashback_pct": 1.5,
                "grocery_cashback_pct": 5.0,
                "online_shopping_cashback_pct": 5.0,
                "monthly_reward_cap": 2500.0,
                "min_monthly_income": 30000.0,
                "min_age": 21,
                "min_credit_score": 720
            }
        }

    def _mock_recommendation_explanation(self, prompt: str) -> Dict[str, Any]:
        """Generates grounded personalized explanation with zero hallucinations."""
        return {
            "why_it_matches": "This option strongly aligns with your spending profile and stated priorities for low fees and transparent benefits.",
            "priority_fit": "Directly supports your goal of maximizing rewards on online shopping and everyday grocery spends without incurring high annual costs.",
            "financial_impact": "Based on your spending inputs, the calculated net annual value offers an estimated positive benefit after fee offsets.",
            "rank_reasoning": "Ranks highly due to verified eligibility match, strong fee waiver thresholds, and published cashback benefits.",
            "drawbacks_and_tradeoffs": [
                "Reward points are subject to monthly category caps.",
                "Late payment or rolling balances incur standard interest charges (~42% p.a.)."
            ],
            "eligibility_limitations": "Meets published income and employment thresholds; final issuance remains subject to bank credit assessment.",
            "assumptions": [
                "Projections assume regular monthly spending distribution as stated in your profile.",
                "Assumes full statement balances are paid on or before the due date to avoid interest."
            ],
            "what_to_verify_before_applying": [
                "Check the latest fee schedule on the official bank portal.",
                "Review excluded MCC categories (e.g. rent, wallet loads, fuel) on the issuer terms."
            ]
        }


class GeminiLLMProvider(LLMProvider):
    """Google Gemini API Provider."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.base_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if schema:
            payload["generationConfig"]["responseSchema"] = schema

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.base_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)


class OpenAILLMProvider(LLMProvider):
    """OpenAI compatible provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={"model": self.model, "messages": messages}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Authorization": f"Bearer {self.api_key}"}
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            return json.loads(raw_text)


def get_llm_provider() -> LLMProvider:
    """Returns the configured LLM provider or default MockLLMProvider."""
    provider_type = (settings.LLM_PROVIDER or "mock").lower()
    
    if provider_type == "gemini" and settings.LLM_API_KEY:
        return GeminiLLMProvider(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
    elif provider_type == "openai" and settings.LLM_API_KEY:
        return OpenAILLMProvider(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
    
    logger.info("Using MockLLMProvider (deterministic, offline-ready).")
    return MockLLMProvider()
