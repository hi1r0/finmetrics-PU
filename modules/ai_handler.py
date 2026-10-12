import logging
from typing import List
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AIHandler:
    """
    Handles interactions with the Google Gemini API for stock discovery.
    """
    _global_key_index = 0  # Class variable to persist rotation index across instances

    def __init__(self, api_keys: str):
        # Support comma-separated strings or lists of keys
        if isinstance(api_keys, str):
            self.keys = [k.strip() for k in api_keys.split(",") if k.strip()]
        elif isinstance(api_keys, list):
            self.keys = [k.strip() for k in api_keys if k.strip()]
        else:
            self.keys = []
            
        if not self.keys:
            raise ValueError("No valid Gemini API keys provided.")
            
        self._configure_next_key()
        self.model_name = self._find_available_model()
        if not self.model_name:
            raise ValueError("No compatible Gemini models found for this API key.")
        
        logger.info(f"AI Search: Using model {self.model_name} with a pool of {len(self.keys)} API keys.")
        self.model = genai.GenerativeModel(self.model_name)

    def _configure_next_key(self):
        """Cycles to the next key in the pool and configures the SDK."""
        if not self.keys:
            return
        idx = AIHandler._global_key_index % len(self.keys)
        key = self.keys[idx]
        genai.configure(api_key=key)
        logger.info(f"AI Search: Active API Key rotated to key index {idx} ({key[:8]}...)")
        AIHandler._global_key_index = (idx + 1) % len(self.keys)

    def _find_available_model(self) -> str:
        """Dynamically finds the best available model for the given API key."""
        available_models = []
        try:
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    available_models.append(m.name)
            
            # Prefer 2.5 flash, 2.0 flash, 1.5 flash, then pro, then whatever is available
            for pref in ["models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro"]:
                if pref in available_models:
                    return pref
                    
            if available_models:
                return available_models[0]
                
        except Exception as e:
            logger.warning(f"Failed to list models: {e}")
            
        return "gemini-1.5-flash" # Fallback

    def _safe_extract_text(self, response) -> str:
        """
        Safely extracts text from the generation response, avoiding ValueError exceptions
        caused by response.text quick accessor when candidates are empty or blocked.
        """
        if not response:
            return ""
        
        try:
            # First, check if response has candidates and they are not empty
            if not hasattr(response, "candidates") or not response.candidates:
                logger.warning("AI safe text extraction: No candidates found in the response.")
                return ""
            
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, "finish_reason", None)
            
            # If the candidate has content and parts, extract from them directly
            if hasattr(candidate, "content") and candidate.content and hasattr(candidate.content, "parts") and candidate.content.parts:
                parts = candidate.content.parts
                text_parts = []
                for p in parts:
                    if hasattr(p, "text") and p.text:
                        text_parts.append(p.text)
                if text_parts:
                    return "".join(text_parts).strip()
            
            # Try response.text as a fallback if the parts check failed or text_parts is empty
            try:
                if hasattr(response, "text") and response.text:
                    return response.text.strip()
            except Exception as tex:
                logger.warning(f"Failed to access response.text directly: {tex}")
                
            logger.warning(f"AI safe text extraction: No valid text parts found in candidates. Finish reason: {finish_reason}")
            if hasattr(candidate, "safety_ratings"):
                logger.warning(f"Safety ratings: {candidate.safety_ratings}")
                
        except Exception as e:
            logger.warning(f"Error in safe text extraction: {e}")
            
        return ""

    def search_industry_tickers(self, query: str, market: str = "NSE India") -> List[str]:
        """
        Uses Gemini to discover high-precision stock tickers for a given industry in a specific market.
        """
        prompt = f"""
Task:
List all actively traded common stock tickers for companies primarily operating in the [{query}] industry in [{market}].

Instructions:
- Return ONLY ticker symbols
- Output one ticker per line using `\\n`
- Do NOT include company names
- Do NOT include numbering, bullets, markdown, tables, headings, or explanations
- Do NOT include duplicate tickers
- Include ONLY currently active and publicly traded companies
- Exclude delisted, suspended, bankrupt, acquired, merged, inactive, or private companies
- Exclude ETFs, mutual funds, index funds, closed-end funds, trusts, ADR duplicates, ETNs, REITs (unless the industry itself is REITs), SPACs, shell companies, preferred shares, warrants, rights, units, bonds, and convertible securities
- Include only standard/common equity shares

Industry Filtering:
- Include only companies whose primary business activity directly matches the requested industry/sector
- Exclude loosely related, diversified, or adjacent businesses unless the requested industry is their core operating segment
- Prefer pure-play companies whenever possible
- Exclude companies with only minor exposure to the industry

Ticker Formatting:
- Use Yahoo Finance ticker formatting exactly
- Apply the correct Yahoo Finance exchange suffix for the requested market/country
- Examples:
  - USA → no suffix
  - India NSE → .NS
  - India BSE → .BO
  - Toronto → .TO
  - London → .L
  - Australia → .AX
  - Hong Kong → .HK
  - Japan → .T
  - Paris → .PA
  - Germany XETRA → .DE
  - Switzerland → .SW

Validation Rules:
- Verify each ticker is actively listed on the specified exchange
- Verify the ticker belongs to the requested market/country
- Do not invent or guess tickers
- Do not output explanatory text under any circumstance

Required Output Format Example:
AAPL
MSFT
GOOGL
"""
        max_attempts = max(1, len(self.keys))
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"AI Search: Querying Gemini for '{query}' (Attempt {attempt + 1}/{max_attempts})")
                # Rotate API key and refresh model instance dynamically to pick up new configuration
                self._configure_next_key()
                self.model = genai.GenerativeModel(self.model_name)
                
                # Configure permissive safety thresholds for professional financial/industry queries
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ]
                
                response = self.model.generate_content(prompt, safety_settings=safety_settings)
                
                # Safe text extraction to avoid ValueError exceptions when parts are empty
                raw_text = self._safe_extract_text(response)
                
                if not raw_text:
                    logger.warning(f"AI Search: Empty response from Gemini on attempt {attempt + 1}.")
                    if attempt < max_attempts - 1:
                        logger.info("AI Search: Trying next API key due to empty or blocked response.")
                        continue
                    return []
                
                # Handle potential markdown code blocks
                if "```" in raw_text:
                    segments = raw_text.split("```")
                    if len(segments) > 1:
                        raw_text = segments[1]
                        if raw_text.startswith("text"):
                            raw_text = raw_text[4:]
                
                # Normalize: Replace literal \n string with real newlines
                raw_text = raw_text.replace("\\n", "\n")
                
                # Split by real newlines and clean up
                lines = []
                for line in raw_text.split("\n"):
                    # Remove any trailing colons, commas, or quotes
                    cleaned = line.strip().strip(":").strip(",").strip('"').strip("'")
                    if cleaned:
                        lines.append(cleaned.upper())
                
                # Return cleaned uppercase lines (AI should have added suffixes)
                valid_tickers = [t.upper() for t in lines if t]
                
                logger.info(f"AI Search: Found {len(valid_tickers)} tickers for '{query}' in {market}")
                return valid_tickers
                
            except Exception as e:
                last_exception = e
                logger.warning(f"AI Search attempt {attempt + 1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    logger.info("AI Search: Rotating to next API key for retry.")
                else:
                    logger.error(f"AI Search: All {max_attempts} keys in the pool failed.")
                    raise last_exception

