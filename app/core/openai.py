from typing import Optional
from openai import AsyncOpenAI, AsyncAzureOpenAI
import logging
from .config import get_settings

logger = logging.getLogger(__name__)

def get_openai_client():
    """Initialize and return OpenAI client based on environment settings"""
    settings = get_settings()
    
    if settings.OPENAI_TYPE == "azure":
        if not all([
            settings.AZURE_OPENAI_ENDPOINT,
            settings.AZURE_OPENAI_KEY,
            settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        ]):
            raise ValueError(
                "Missing required Azure OpenAI configuration. Please ensure AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_KEY, and AZURE_OPENAI_CHAT_DEPLOYMENT are set in your environment."
            )

        # Fix endpoint formatting - remove /models if present
        endpoint = settings.AZURE_OPENAI_ENDPOINT
        if '/models' in endpoint:
            endpoint = endpoint.split('/models')[0]
            
        # Log detailed configuration 
        logger.info(f"Setting up Azure OpenAI client with:")
        logger.info(f"- Endpoint: {endpoint}")
        logger.info(f"- API Version: {settings.AZURE_OPENAI_VERSION}")
        logger.info(f"- Deployment: {settings.AZURE_OPENAI_CHAT_DEPLOYMENT}")
        
        return AsyncAzureOpenAI(
            api_version=settings.AZURE_OPENAI_VERSION,
            azure_endpoint=endpoint,
            api_key=settings.AZURE_OPENAI_KEY,
            azure_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        )
    else:
        if not settings.OPENAI_API_KEY:
            raise ValueError("Missing OPENAI_API_KEY for regular OpenAI configuration")

        logger.info("Setting up regular OpenAI client")
        return AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )