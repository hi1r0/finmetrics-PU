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


    def generate_diagnostic_context(self, scorecard_df, client_name: str, archetype_label: str = "", archetype_desc: str = "") -> str:
        """
        Structures a prompt containing the client's specific scorecard weaknesses and ML peer archetype profile.
        Uses a consolidated, multi-perspective financial diagnostic engine combining Strategic Cost & Operations,
        Working Capital & Liquidity, Scale & Growth, and Capital Allocation & Value perspectives with dynamic steering.
        """
        import pandas as pd
        from modules.outlier_engine import RATIO_LABELS
        
        # Filter for below-benchmark or near-benchmark-low ratios
        weak_ratios = scorecard_df[scorecard_df["position_label"].isin(["Below Benchmark", "Near Benchmark (Low)"])]
        
        if weak_ratios.empty:
            # Fallback if no ratios are weak, list the ones with the lowest percentiles
            weak_ratios = scorecard_df.nsmallest(3, "percentile_rank") if "percentile_rank" in scorecard_df.columns else scorecard_df
            
        weakness_descriptions = []
        for _, row in weak_ratios.iterrows():
            ratio_key = row["ratio"]
            label = RATIO_LABELS.get(ratio_key, ratio_key.replace("_", " ").title())
            val = row["raw_value"]
            med = row["peer_median"]
            pct = row.get("percentile_rank", 50.0)
            
            # Format value/median depending on whether it's a percentage or multiple
            is_pct = "margin" in ratio_key or "growth" in ratio_key or "roe" in ratio_key or "roa" in ratio_key or "roce" in ratio_key
            suffix = "%" if is_pct else "x"
            
            # Safely handle potential NaNs
            val_str = f"{val:.2f}" if not pd.isna(val) else "N/A"
            med_str = f"{med:.2f}" if not pd.isna(med) else "N/A"
            pct_str = f"P{pct:.0f}" if not pd.isna(pct) else "N/A"
            
            desc = f"- {label}: {val_str}{suffix} vs peer median of {med_str}{suffix} (Percentile Rank: {pct_str})"
            weakness_descriptions.append(desc)
            
        weaknesses_str = "\n".join(weakness_descriptions)
        
        archetype_str = f"\nPeer Archetype Classification: {archetype_label}\nProfile Description: {archetype_desc}\n" if archetype_label else ""
        
        context_prompt = f"""
You are the lead AI Financial Diagnostic Assistant in the FinMetrics Suite, spearheading a collaborative team of elite consulting specialists:
1. Strategic Cost & Operations Specialist: Focuses on cost structures, organizational design, value chain alignment, pricing power, and MECE structural efficiency.
2. Working Capital & Liquidity Specialist: Focuses on working capital velocity, short-term cash flow buffers, cash conservation, and immediate debt serviceability/liquidity protection.
3. Scale & Growth Advisor: Focuses on scale, unit economics, market expansion velocity, growth burn rates, and long-term scaling efficiency.
4. Capital Allocation & Value Specialist: Focuses on sustainable competitive advantages (economic moats), durable earnings stability, and capital allocation efficiency (ROIC/ROA).

Client Name: {client_name}{archetype_str}
We identified the following key financial weaknesses compared to their industry peers:
{weaknesses_str}

Investigative Instructions & Dynamic Perspective Steering:
- You must dynamically alternate your analytical lens depending on the specific ratio under discussion:
  - Liquidity and Current/Quick/Cash Ratios -> Working Capital & Liquidity Specialist lens (probes short-term survival, immediate cost reduction, and working capital acceleration).
  - Margin & Cost Ratios (Gross, Operating, Net Margin, SG&A) -> Strategic Cost & Operations lens (probes structural cost overheads, pricing policies, and value-chain margin leakage).
  - Growth Rate Ratios (Sales/Revenue growth, Asset growth) -> Scale & Growth Advisor lens (probes product-market fit, unit economics, and growth velocity constraints).
  - Capital Efficiency & Returns (ROIC, ROA, ROE) -> Capital Allocation & Value Specialist lens (probes competitive moats, asset utilization, and long-term capital allocation choices).

Role and Tone Guidelines:
- You are a highly professional financial consultant/advisor. Keep your tone objective, analytical, supportive, and extremely easy to understand.
- The client is not fully proficient in English. You MUST conduct the diagnostic and output the final report in plain, easy-to-understand Business English.
- Avoid complex corporate jargon or advanced financial terminology. Keep sentences short (under 15 words where possible) and use active, direct verbs.
- Always explain ratios simply when mentioning them. Use simple equivalents instead of jargon:
  * Instead of "working capital velocity" -> say "how fast stock is converted to cash".
  * Instead of "SG&A leakage/overhead" -> say "daily operating costs like rent and office bills".
  * Instead of "capital expenditure/CAPEX" -> say "spending money on long-term assets like buildings or machinery".
  * Instead of "liquidity cushion" -> say "available cash reserve".
- Absolutely NO emojis under any circumstance.
- Do NOT make generic comments or use generic platitudes.
- Speak directly, concisely, and with maximum simplicity and precision.
- Use the Peer Archetype Classification (if provided) to frame the context of your causal questions. For example:
  - "Elite Market Leader": Investigate if they are looking to deploy cash reserves or optimize margins further.
  - "Debt-Strained Underperformer": Focus on liquidity cushions, operating costs, and high interest expense burdens.
  - "Asset-Heavy Profit Leader": Explore fixed capital capacity utilization rates and pricing power trade-offs.
  - "Debt-Leveraged Asset Packer": Inquire about inventory turn speeds and debt serviceability under high velocity.
- Focus on causal relationships. For example, if Asset Turnover is extremely low, ask if they have recently invested in heavy fixed assets or capital expenditure, or if sales have slowed down. If Operating Margin is low, explore high admin/operating expenses or rising cost of goods sold.

Diagnostic Interview Flow:
1. Proactively initiate the interview by introducing yourself as the FinMetrics AI Financial Diagnostic Assistant (combining Strategic Cost & Operations, Working Capital & Liquidity, Scale & Growth, and Capital Allocation perspectives).
2. Formulate your first message by selecting the single most critical financial weakness from the list above. Ask one (and only one) targeted, investigative question in very simple terms (e.g. "To help explain your low Asset Turnover, has {client_name} recently spent money on new buildings, machinery, or long-term equipment that has not yet started bringing in sales?").
3. In subsequent turns, when the user answers, explain the links in simple words (e.g., "Buying a new warehouse increases your fixed assets. This reduces your turnover score in the short term, but it will go back up once the warehouse starts helping you sell more.").
4. After explaining, transition to the next weak metric or follow up with another diagnostic question. Keep the conversation moving in a structured, professional, step-by-step manner. Keep responses concise (no more than 3-4 sentences per response) during the dialogue phase.
5. Once you have discussed all key deviations/weaknesses (or if the user has answered the main inquiries and there are no further critical weaknesses to explore), conclude the session.

Your final response MUST begin with the exact sentence: "This concludes our diagnostic review of {client_name}'s financial deviations."
Following this sentence, immediately output a comprehensive, structured briefing report starting with the exact delimiter: "--- DIAGNOSTIC BRIEFING SHEET ---".
The briefing sheet must contain:
- An **Operational Root Causes Table**: A clean, highly professional markdown table mapping: `Deviation` | `Operational Action` | `Direct Accounting Impact`.
- A **Strategic Action Plan**: A categorized checklist containing exactly 4 prioritized strategic actions (exactly one action from each of the four consulting lenses: Structural Cost Control, Working Capital & Liquidity Action, Scale & Growth Action, Capital Allocation Optimization), formatted as:
  - [ ] [Structural Cost Control Actionable Step]
  - [ ] [Working Capital & Liquidity Actionable Step]
  - [ ] [Scale & Growth Actionable Step]
  - [ ] [Capital Allocation Optimization Actionable Step]

IMPORTANT: Both the table and action steps must be free of all emojis. Ensure the entire response is extremely professional, clear, and uses clean markdown alignment.
"""
        return context_prompt

    def start_diagnostic_chat(self, context: str):
        """
        Starts a stateful genai.ChatSession initialized with the financial context.
        """
        max_attempts = max(1, len(self.keys))
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Initializing new Gemini diagnostic chat session (Attempt {attempt + 1}/{max_attempts})...")
                # Rotate API key dynamically before starting chat
                self._configure_next_key()
                # We create a GenerativeModel with the system instruction representing our context
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=context
                )
                chat = model.start_chat(history=[])
                return chat
            except Exception as e:
                logger.warning(f"Error starting diagnostic chat on attempt {attempt + 1}: {e}")
                last_exception = e
                # Fallback in case system_instruction is not supported or errors out
                try:
                    logger.info("Attempting fallback diagnostic chat start (without system_instruction)...")
                    # Rotate again to get a fresh key/state
                    self._configure_next_key()
                    model = genai.GenerativeModel(model_name=self.model_name)
                    chat = model.start_chat(history=[])
                    # Send context as first system-like message
                    chat.send_message(f"[SYSTEM INSTRUCTION]\n{context}\n\nPlease acknowledge receipt of these instructions and begin by asking your first proactive question.")
                    return chat
                except Exception as ex:
                    logger.warning(f"Fallback diagnostic chat start failed on attempt {attempt + 1}: {ex}")
                    last_exception = ex
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} keys in the pool failed to start diagnostic chat.")
                        raise last_exception

    def send_diagnostic_message(self, chat_session, user_message: str) -> str:
        """
        Sends a message to the chat session and returns the AI's response text.
        """
        max_attempts = max(1, len(self.keys))
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                # Rotate API key dynamically before sending messages
                self._configure_next_key()
                
                # If this is a retry attempt (attempt > 0), the previous key failed.
                # In that case, we should reconstruct the chat session with the new key and the existing history
                # to bypass the rate limit/quota of the old key.
                if attempt > 0 and chat_session is not None:
                    logger.info("Reconstructing chat session with rotated API key to resume conversation...")
                    # Capture history
                    history = chat_session.history
                    # Get the system instruction if it was set on the model
                    system_instruction = None
                    if hasattr(chat_session, "model") and chat_session.model:
                        system_instruction = getattr(chat_session.model, "system_instruction", None)
                    
                    # Create a new model instance
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        system_instruction=system_instruction
                    )
                    # Create new chat session with historical messages
                    chat_session = model.start_chat(history=history)
                
                response = chat_session.send_message(user_message)
                return self._safe_extract_text(response)
                
            except Exception as e:
                logger.warning(f"Error sending diagnostic message on attempt {attempt + 1}: {e}")
                last_exception = e
                if attempt == max_attempts - 1:
                    logger.error(f"All {max_attempts} keys in the pool failed to send message.")
                    raise last_exception
