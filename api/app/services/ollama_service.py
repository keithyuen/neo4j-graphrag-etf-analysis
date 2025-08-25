import httpx
import structlog
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import json

logger = structlog.get_logger()

class OllamaService:
    def __init__(self, host: str, model: str = "mistral:instruct"):
        self.host = host.rstrip('/')
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(
        self, 
        prompt: str, 
        temperature: float = 0.2, 
        max_tokens: int = 500,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using Ollama API."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = await self.client.post(
                f"{self.host}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            generated_text = result.get("response", "").strip()
            
            logger.info("Ollama generation completed",
                       model=self.model,
                       prompt_length=len(prompt),
                       response_length=len(generated_text),
                       temperature=temperature)
            
            return generated_text
            
        except Exception as e:
            logger.error("Ollama generation failed", 
                        error=str(e), 
                        model=self.model,
                        prompt=prompt[:100])
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = await self.client.get(f"{self.host}/api/version")
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.info("Ollama health check passed", host=self.host)
            else:
                logger.warning("Ollama health check failed", 
                              host=self.host, 
                              status_code=response.status_code)
            
            return is_healthy
        except Exception as e:
            logger.error("Ollama health check error", error=str(e), host=self.host)
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Ollama client closed")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()