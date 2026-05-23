# app/core/embeddings.py

from typing import Optional, Union, List
from openai import AsyncOpenAI, AsyncAzureOpenAI

async def compute_text_embedding(
    text: str,
    openai_client: Union[AsyncOpenAI, AsyncAzureOpenAI],
    embed_model: str,
    embed_deployment: Optional[str] = None,
    embedding_dimensions: Optional[int] = None,
) -> List[float]:
    """Compute embeddings for text using OpenAI"""
    try:
        # For Azure, use deployment name as model
        model_name = embed_deployment if embed_deployment else embed_model
        
        embedding = await openai_client.embeddings.create(
            model=model_name,
            input=text
        )
        
        return embedding.data[0].embedding
        
    except Exception as e:
        print(f"Error computing embedding: {str(e)}")
        raise