import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from core.config import get_settings
from core.openai import get_openai_client  # Import our fixed client function

# Import our components
from rag.rag_advanced import AdvancedRAGChat
from rag.postgres_searcher import MarketResearchSearcher
from models.api_models import (
    ChatRequest, 
    ChatRequestContext, 
    ChatRequestOverrides,
    RetrievalMode,
    AIChatRoles,
    Message,
    RAGContext,
    Intent
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(override=True)

async def test_queries():
    settings = get_settings()
    """Test different types of market research queries"""
    
    # Use our fixed OpenAI client function
    client = get_openai_client()
    
    # Initialize database session
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Initialize searcher
    searcher = MarketResearchSearcher(
        db_session=db,
        openai_embed_client=client,
        embed_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        embed_model="text-embedding-ada-002",
        embed_dimensions=1536,
        embedding_column="embedding"
    )
    
    # Initialize RAG with user context for testing
    test_user_context = {
        "org_name": "Doriot",
        "category_list": ["AI", "Fintech"],
        "description": "AI-powered market fundraising platform",
        "org_region": "Edinburgh",
        "org_country_code": "UK"
    }
    
    # Initialize RAG
    rag = AdvancedRAGChat(
        searcher=searcher,
        openai_client=client,
        chat_model="gpt-4",
        chat_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
        user_context=test_user_context  # Add user context
    )
    
    # Test queries including some that might trigger backup model
    test_cases = [
                {
            "category": "Startup Queries",
            "queries": [
                # "What's my startup's profile?",
                "Find me healthcare investors in europe",
                # f"What's {test_user_context['org_name']}'s market position?",
                # "Find investors for my startup",
                # "Recommend investors that match our company profile",
                # "Who are potential investors for my business?",
                # "Analyze my startup's competitors"
            ]
        },
        # {
        #     "category": "Company Profiles",
        #     "queries": [
        #         "What's Doriot's company profile?",
        #         # "Tell me about SpaceX's recent developments",  # Might trigger backup model
        #         # "Analyze the competitive landscape for Tesla"  # Might trigger backup model
        #     ]
        # },
        # {
        #     "category": "Market Analysis",
        #     "queries": [
        #         "What are the key trends in quantum computing?",  # Likely to trigger backup model
        #         "Analyze the future of autonomous vehicles"  # Likely to trigger backup model
        #     ]
        # }
    ]
    
    # Run tests
    for case in test_cases:
        logger.info(f"\nTesting {case['category']} queries:")
        for query in case['queries']:
            try:
                logger.info(f"\nQuery: {query}")
                
                # Create chat request with proper models
                request = ChatRequest(
                    messages=[{
                        "role": AIChatRoles.USER,
                        "content": query
                    }],
                    context=ChatRequestContext(
                        overrides=ChatRequestOverrides(
                            top=3,
                            temperature=0.3,
                            retrieval_mode=RetrievalMode.HYBRID,
                            use_advanced_flow=True
                        )
                    )
                )
                
                # Get parameters and detect intent
                chat_params = await rag.get_params(
                    request.messages, 
                    request.context.overrides,
                    request.context.user_context  # Pass user context
                )
                logger.info(f"Detected Intent: {chat_params.intent}")
                logger.info(f"Confidence: {chat_params.confidence:.2f}")
                
                # Get context and response
                contextual_messages, results, thoughts = await rag.prepare_context(chat_params)
                
                # Log thought process
                logger.info("\nThought Process:")
                for thought in thoughts:
                    logger.info(f"- {thought.title}: {thought.description}")
                
                # Get final response
                response = await rag.answer(
                    chat_params,
                    contextual_messages,
                    results,
                    thoughts
                )
                
                # Log response details
                logger.info("\nResponse:")
                logger.info(response.message.content)
                
                # Log data sources
                # Log data sources
                if response.context.structured_data:
                    logger.info("\nStructured Data Sources:")
                    for data in response.context.structured_data:
                        if isinstance(data, dict):
                            logger.info(f"- Table: {data.get('table', 'Unknown')}")
                        else:
                            logger.info(f"- Table: {data.table}")
                                        
                if response.context.articles:
                    logger.info("\nArticle Sources:")
                    for article in response.context.articles:
                        if isinstance(article, dict):
                            logger.info(f"- {article.get('url')} ({article.get('published_at')})")
                        else:
                            logger.info(f"- {article.url} ({article.published_at})")
                
                # Log if backup model was used
                if any(thought.title == "Backup Research" for thought in response.context.thoughts):
                    logger.info("\nBackup Model Used: DeepSeek-R1")
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}", exc_info=True)
                continue
            
            logger.info("\n" + "="*50)
    
    # Clean up
    db.close()


async def test_streaming():
    settings = get_settings()
    """Test streaming responses from RAG system"""
    
    # Use our fixed OpenAI client function
    client = get_openai_client()
    
    # Initialize database session
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Initialize searcher
    searcher = MarketResearchSearcher(
        db_session=db,
        openai_embed_client=client,
        embed_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        embed_model="text-embedding-ada-002",
        embed_dimensions=1536,
        embedding_column="embedding"
    )
    
    # Initialize RAG with user context for testing
    test_user_context = {
        "org_name": "Doriot",
        "category_list": ["AI", "Fintech"],
        "description": "AI-powered market fundraising platform",
        "org_region": "Edinburgh",
        "org_country_code": "UK"
    }
    
    # Initialize RAG
    rag = AdvancedRAGChat(
        searcher=searcher,
        openai_client=client,
        chat_model="gpt-4",
        chat_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
        user_context=test_user_context  # Add user context
    )
    
    # Test queries including some that might trigger backup model
    test_cases = [
        #         {
        #     "category": "Startup Queries",
        #     "queries": [
        #         # "What's my startup's profile?",
        #         "Tell me about my company",
        #         # f"What's {test_user_context['org_name']}'s market position?",
        #         # "Find investors for my startup",
        #         # "Recommend investors that match our company profile",
        #         # "Who are potential investors for my business?",
        #         # "Analyze my startup's competitors"
        #     ]
        # },
        {
            "category": "Company Profiles",
            "queries": [
                # "Recommend investors for me"
                # "Hello"
                # "What's Doriot's company profile?",
                # "Find me healthcare investors in europe",
                # "Hi",  # Might trigger backup model
                "What's the growth story of Stripe?"  # Might trigger backup model
            ]
        },
        # {
        #     "category": "Market Analysis",
        #     "queries": [
        #         "What are the key trends in quantum computing?",  # Likely to trigger backup model
        #         "Analyze the future of autonomous vehicles"  # Likely to trigger backup model
        #     ]
        # }
    ]
    
    # ... keep existing initialization code until the query loop ...
    
    for case in test_cases:
        logger.info(f"\nTesting {case['category']} streaming queries:")
        for query in case['queries']:
            try:
                logger.info(f"\nQuery: {query}")
                
                # Create chat request
                request = ChatRequest(
                    messages=[{
                        "role": AIChatRoles.USER,
                        "content": query
                    }],
                    context=ChatRequestContext(
                        overrides=ChatRequestOverrides(
                            top=3,
                            temperature=0.3,
                            retrieval_mode=RetrievalMode.HYBRID,
                            use_advanced_flow=True
                        )
                    )
                )
                
                # Get parameters and detect intent
                chat_params = await rag.get_params(
                    request.messages, 
                    request.context.overrides,
                    request.context.user_context
                )
                logger.info(f"Detected Intent: {chat_params.intent}")
                logger.info(f"Confidence: {chat_params.confidence:.2f}")
                
                # Get context
                contextual_messages, results, thoughts = await rag.prepare_context(chat_params)
                
                # Log thought process
                logger.info("\nThought Process:")
                for thought in thoughts:
                    logger.info(f"- {thought.title}: {thought.description}")
                
                # Test streaming response
                logger.info("\nStreaming Response:")
                full_response = ""
                async for chunk in rag.answer_stream(
                    chat_params,
                    contextual_messages,
                    results,
                    thoughts
                ):
                    # Handle context chunk
                    if chunk.context:
                        if chunk.context.structured_data:
                            logger.info("\nStructured Data Sources:")
                            for data in chunk.context.structured_data:
                                if isinstance(data, dict):
                                    logger.info(f"- Table: {data.get('table', 'Unknown')}")
                                else:
                                    logger.info(f"- Table: {data.table}")
                        
                        if chunk.context.articles:
                            logger.info("\nArticle Sources:")
                            for article in chunk.context.articles:
                                if isinstance(article, dict):
                                    logger.info(f"- {article.get('url')} ({article.get('published_at')})")
                                else:
                                    logger.info(f"- {article.url} ({article.published_at})")
                    
                    # Handle content chunks
                    if chunk.delta:
                        content = chunk.delta.content
                        print(content, end="", flush=True)  # Stream to console
                        full_response += content
                
                print("\n")  # New line after streaming complete
                
                # Log if backup model was used
                if any(thought.title == "Backup Research" for thought in thoughts):
                    logger.info("\nBackup Model Used: DeepSeek-R1")
                
            except Exception as e:
                logger.error(f"Error processing streaming query '{query}': {str(e)}", exc_info=True)
                continue
            
            logger.info("\n" + "="*50)

async def main():
    load_dotenv()
    # await test_queries()
    await test_streaming() 

if __name__ == "__main__":
    asyncio.run(main())