import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool
from qdrant_client import AsyncQdrantClient

from app.config import settings
from app.services.embedding import EmbeddingService
from app.services.retrieval import RetrievalService
from app.services.llm import LLMService


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.qdrant = AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )

    app.state.embedding = EmbeddingService(
        settings.embedding_model
    )

    app.state.retrieval = RetrievalService(
        app.state.qdrant,
        settings.qdrant_collection
    )

    app.state.llm = LLMService(
        settings.openrouter_api_key,
        settings.openrouter_base_url,
        settings.openrouter_model
    )

    yield

    await app.state.qdrant.close()
    await app.state.llm.client.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):

    await websocket.accept()

    try:

        while True:

            # Receive question and frontend conversation history
            data = await websocket.receive_json()

            question = data["message"]
            history = data.get("history", [])
            top_k = data.get("top_k", settings.top_k)

            try:

                # 1. Generate embedding
                embedding = await run_in_threadpool(
                    websocket.app.state.embedding.embed_query,
                    question
                )

                # 2. Retrieve relevant documents
                documents = await websocket.app.state.retrieval.retrieve(
                    embedding,
                    top_k
                )

                # 3. Build RAG context
                context = "\n\n".join(
                    f"[{i}] {doc['text']}"
                    for i, doc in enumerate(documents, 1)
                )

                # 4. Construct prompt
                system_prompt = f"""
You are a DarGlobal Assistant, DARGI. Your sole purpose is to answer questions strictly related to DarGlobal—such as its luxury real estate developments, projects, and investment opportunities. 

DarGlobal is a premier international luxury real estate investment and development platform specialising in architecturally distinctive, design-led residences in the world's most sought-after destinations. Listed on the London Stock Exchange, it connects global capital with curated luxury living and property investment opportunities across the UAE, Saudi Arabia, Qatar, Spain, and beyond.

Instructions:
1. Strict Scope: Answer ONLY queries related to DarGlobal. If a user asks about anything unrelated to DarGlobal (e.g., general knowledge, competitors, unrelated topics), politely decline and state that you can only assist with DarGlobal-related inquiries.
2. Context & Chat History Reliance: Rely exclusively on the retrieved context and the ongoing chat history to answer questions. Extract and use ONLY the specific details relevant to the user's current query—ignore and omit any irrelevant information from the context or previous messages.
3. Fallback & No Hallucinations: Do not invent, assume, or extrapolate information beyond the retrieved context and chat history. If neither contains the relevant information to answer a DarGlobal-related query, inform the user that you do not have relevant information to answer the query and direct them to contact the team via:
   - Phone: +971 4562 9616
   - WhatsApp: 97180040409
4. Conciseness: Keep every response brief, direct, and to the point. Avoid unnecessary fluff, filler, or overly verbose explanations.
                """

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]

                messages.extend(
                    history[-settings.max_history_messages:]
                )

                user_content = f"""
Use the following retrieved context to answer the question.

Retrieved Context:
{context}

User Question:
{question}
"""

                messages.append({
                    "role": "user",
                    "content": user_content
                })

                # 5. Send retrieved sources
                await websocket.send_json({
                    "type": "sources",
                    "sources": documents
                })

                # 6. Stream LLM response
                async for token in websocket.app.state.llm.stream_response(
                    messages
                ):

                    await websocket.send_json({
                        "type": "token",
                        "content": token
                    })

                # 7. Signal completion
                await websocket.send_json({
                    "type": "done"
                })

            except Exception:

                logger.exception("Chat processing failed")

                await websocket.send_json({
                    "type": "error",
                    "message": "Unable to generate response"
                })

    except WebSocketDisconnect:

        logger.info("WebSocket client disconnected")