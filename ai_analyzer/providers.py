"""
AI Provider with Robust JSON Parsing & Cost Calculation
Verified & Tested: Dec 2025
Model: gemini-flash-latest
"""

import google.generativeai as genai
from django.conf import settings
import json
import re
import time


class AIProvider:
    """Base class"""
    def analyze(self, keyword, links, titles):
        raise NotImplementedError


class GeminiProvider(AIProvider):
    """Gemini Provider with Robust JSON Parsing"""
    
    SYSTEM_INSTRUCTION = """You are a strictly technical SEO data extractor.
Your ONLY task is to return a JSON object based on the user input.
NO intro text. NO outro text. NO markdown formatting (like ```json).
Start your response with '{' and end with '}'.

Required JSON Structure:
{
  "intent": "Select from allowed Intent Mapping values (see below)",
  "type": "Select from allowed Search Intent values (see below)"
}

Intent Mapping Options (select ONE or COMBINATION):
- Informational
- Navigational
- Commercial
- Transactional
- Commercial-Transactional
- Informational-Commercial

Search Intent Options (select ONE):
- product category
- product
- blog
- page-landing

Guidelines:
- Intent Mapping: Can be single or hyphenated combination
- Search Intent: Must be exactly one of the 4 options
- Use lowercase for "product category", "product", "blog", "page-landing"
- Use proper case for Intent Mapping (e.g., "Commercial-Transactional")

Examples:
{"intent": "Commercial-Transactional", "type": "product category"}
{"intent": "Informational", "type": "blog"}
{"intent": "Transactional", "type": "product"}
{"intent": "Navigational", "type": "page-landing"}
{"intent": "Informational-Commercial", "type": "blog"}"""
    
    PRICE_PER_1M_INPUT = 0.075
    PRICE_PER_1M_OUTPUT = 0.30

    def __init__(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        self.model = genai.GenerativeModel(
            'models/gemini-flash-latest', 
            system_instruction=self.SYSTEM_INSTRUCTION,
            safety_settings=safety_settings
        )
        
        print("✅ Gemini Flash Provider Initialized (Robust Mode)")
    
    def analyze(self, keyword, links, titles):
        """Analyzes keyword intent with cost tracking and regex parsing"""
        
        start_time = time.time()
        
        try:
            urls_str = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links[:10])])
            prompt = f"Keyword: {keyword}\nURLs:\n{urls_str}"
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 2000,
                    "response_mime_type": "application/json"
                }
            )
            
            end_time = time.time()
            
            usage = response.usage_metadata
            in_tokens = usage.prompt_token_count
            out_tokens = usage.candidates_token_count
            
            cost_input = (in_tokens / 1_000_000) * self.PRICE_PER_1M_INPUT
            cost_output = (out_tokens / 1_000_000) * self.PRICE_PER_1M_OUTPUT
            total_cost = cost_input + cost_output
            
            print(f"📊 Time: {end_time - start_time:.2f}s | Tokens: {usage.total_token_count} | Cost: ${total_cost:.8f}")

            raw_text = response.text
            match = re.search(r'\{[\s\S]*\}', raw_text)
            
            if match:
                clean_json_text = match.group(0)
                data = json.loads(clean_json_text)
                return data.get('intent', 'N/A'), data.get('type', 'N/A')
            else:
                print(f"❌ No JSON found. Raw: {raw_text[:100]}")
                return "N/A", "N/A"
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return "N/A", "N/A"


class GPTProvider(AIProvider):
    def __init__(self, api_key):
        self.api_key = api_key
    
    def analyze(self, keyword, links, titles):
        return "N/A", "N/A"


class ClaudeProvider(AIProvider):
    def __init__(self, api_key):
        self.api_key = api_key
    
    def analyze(self, keyword, links, titles):
        return "N/A", "N/A"