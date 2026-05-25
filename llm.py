import time
import random
import logging
import requests
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MultiAgentAutoCodingLab")

class LLMClient:
    def __init__(self, gemini_api_key=None, groq_api_key=None, openai_api_key=None, anthropic_api_key=None, custom_api_key=None, custom_api_url=None):
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.custom_api_key = custom_api_key
        self.custom_api_url = custom_api_url
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            
    def call_gemini(self, model_name, system_prompt, prompt, temperature=0.7, max_tokens=None):
        """
        Call Gemini API with exponential backoff for rate limits (429).
        """
        if not self.gemini_api_key:
            raise ValueError("Google Gemini API Key is missing. Please configure it in the sidebar.")
            
        # Configure model
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
            
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
            generation_config=generation_config
        )
        
        max_retries = 5
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                # Apply request size safety check (approximate token/char limits)
                if len(prompt) > 100000:
                    logger.warning("Prompt is very long, truncating to 100k characters.")
                    prompt = prompt[:100000] + "\n...[TRUNCATED BY LLM CLIENT]..."
                    
                response = model.generate_content(prompt)
                return response.text
            except (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable) as e:
                # 429 Rate Limit or 503 Service Unavailable
                delay = base_delay ** attempt + random.uniform(0, 1)
                logger.warning(f"Gemini API rate limited/unavailable. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
            except Exception as e:
                # Other non-retryable exception
                logger.error(f"Error calling Gemini: {e}")
                raise e
                
        raise Exception("Failed to call Gemini API after multiple retries due to rate limiting.")

    def _call_rest_api(self, url, headers, payload, response_parser, provider_name):
        """
        General REST API helper with exponential backoff.
        """
        max_retries = 5
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=90)
                
                # Check for rate limit (429) or transient server errors
                if response.status_code in [429, 502, 503, 504]:
                    delay = base_delay ** attempt + random.uniform(0, 1)
                    logger.warning(f"{provider_name} API returned status {response.status_code}. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                    continue
                    
                # Check for other HTTP errors
                response.raise_for_status()
                
                res_data = response.json()
                return response_parser(res_data)
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error calling {provider_name} API: {e}")
                    raise e
                    
                delay = base_delay ** attempt + random.uniform(0, 1)
                logger.warning(f"Network error calling {provider_name}. Retrying in {delay:.2f}s... Error: {e}")
                time.sleep(delay)
                
        raise Exception(f"Failed to call {provider_name} API after multiple retries.")

    def call_groq(self, model_name, system_prompt, prompt, temperature=0.7, max_tokens=None):
        """
        Call Groq API using requests.
        """
        if not self.groq_api_key:
            raise ValueError("Groq API Key is missing. Please configure it in the sidebar.")
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        return self._call_rest_api(
            url=url,
            headers=headers,
            payload=payload,
            response_parser=lambda data: data["choices"][0]["message"]["content"],
            provider_name="Groq"
        )

    def call_openai(self, model_name, system_prompt, prompt, temperature=0.7, max_tokens=None):
        """
        Call OpenAI API using requests.
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API Key is missing. Please configure it in the sidebar.")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        return self._call_rest_api(
            url=url,
            headers=headers,
            payload=payload,
            response_parser=lambda data: data["choices"][0]["message"]["content"],
            provider_name="OpenAI"
        )

    def call_anthropic(self, model_name, system_prompt, prompt, temperature=0.7, max_tokens=None):
        """
        Call Anthropic API using requests.
        """
        if not self.anthropic_api_key:
            raise ValueError("Anthropic API Key is missing. Please configure it in the sidebar.")
            
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "system": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens if max_tokens else 4000
        }
        
        return self._call_rest_api(
            url=url,
            headers=headers,
            payload=payload,
            response_parser=lambda data: data["content"][0]["text"],
            provider_name="Anthropic"
        )

    def call_custom(self, model_name, system_prompt, prompt, temperature=0.7, max_tokens=None):
        """
        Call custom OpenAI-compatible API endpoint (Ollama, LM Studio, etc.).
        """
        if not self.custom_api_url:
            raise ValueError("Custom Base URL is missing. Please configure it in the sidebar.")
            
        url = self.custom_api_url
        headers = {
            "Content-Type": "application/json"
        }
        if self.custom_api_key:
            headers["Authorization"] = f"Bearer {self.custom_api_key}"
            
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        return self._call_rest_api(
            url=url,
            headers=headers,
            payload=payload,
            response_parser=lambda data: data["choices"][0]["message"]["content"],
            provider_name="Custom API"
        )

    def call_model(self, provider, model_name, system_prompt, prompt, temperature=0.7, max_tokens=None):
        """
        Unified method to call any supported LLM provider.
        """
        provider = provider.lower()
        if provider == "gemini":
            return self.call_gemini(model_name, system_prompt, prompt, temperature, max_tokens)
        elif provider == "groq":
            return self.call_groq(model_name, system_prompt, prompt, temperature, max_tokens)
        elif provider == "openai":
            return self.call_openai(model_name, system_prompt, prompt, temperature, max_tokens)
        elif provider == "anthropic":
            return self.call_anthropic(model_name, system_prompt, prompt, temperature, max_tokens)
        elif provider == "custom":
            return self.call_custom(model_name, system_prompt, prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
