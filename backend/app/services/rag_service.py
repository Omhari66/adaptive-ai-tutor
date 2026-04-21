"""
RAG (Retrieval-Augmented Generation) Service
Handles query rewriting, vector search, reranking, and response generation
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from groq import AsyncGroq
from app.core.config import settings
from app.services.embedding_service import get_embedding_service
from app.core.prompts import get_prompt_for_mode
from app.services.topic_service import get_topic_service
from app.services.learning_state_service import get_learning_state_service
from app.services.evaluation_service import get_evaluation_service

logger = logging.getLogger(__name__)

# Global session tracking
_user_sessions = {}


class RAGService:
    """
    Service for RAG-based question answering.
    Implements query rewriting, vector retrieval, reranking, and LLM generation.
    """

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self._embedding_service = None
        self.topic_service = get_topic_service()
        self.learning_state_service = get_learning_state_service()
        self.evaluation_service = get_evaluation_service()

    def _get_embedding_service(self):
        """Lazy load embedding service singleton"""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def _rewrite_query(
        self,
        query: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Rewrite follow-up queries to be standalone using conversation context.
        Example: "What about the second stage?" -> "What is the second stage of cellular respiration?"
        """
        if not conversation_history:
            return query

        # Build context from conversation
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ])

        prompt = f"""Given the following conversation and a follow-up question, rewrite the question to be standalone and specific.

Conversation:
{context}

Follow-up: {query}

Standalone question:"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a query rewriter. Rewrite follow-up questions to be standalone and specific, without referring to previous conversation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using shared embedding service"""
        embedding_service = self._get_embedding_service()
        return embedding_service.generate_embedding(text)

    async def _search_vectors(
        self,
        query_embedding: List[float],
        document_ids: List[str],
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Search Qdrant vector database for similar chunks.
        Returns top_k results with metadata.
        Logs errors properly instead of silent failures.
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, FieldCondition, MatchAny, VectorParams, Distance

            # Initialize Qdrant client
            if settings.QDRANT_URL == "local":
                client = QdrantClient(path="./qdrant_data")
            else:
                client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )

            # Ensure collection exists before searching
            if not client.collection_exists(collection_name=settings.QDRANT_COLLECTION_NAME):
                # Collection doesn't exist - create it
                logger.info(f"Creating Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")
                client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=384,  # Size for all-MiniLM-L6-v2
                        distance=Distance.COSINE
                    )
                )

            # Build filter for document IDs
            doc_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=document_ids)
                    )
                ]
            ) if document_ids else None

            response = client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_embedding,
                query_filter=doc_filter,
                limit=top_k
            )
            results = response.points

            return [
                {
                    "id": hit.id,
                    "content": hit.payload.get("content", ""),
                    "page": hit.payload.get("page_number", 0),
                    "doc_id": hit.payload.get("document_id", ""),
                    "doc_name": hit.payload.get("document_name", ""),
                    "score": hit.score
                }
                for hit in results
            ]
        except ImportError as e:
            logger.error(f"Qdrant client not installed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            raise e

    async def _search_sequential(
        self,
        document_ids: List[str],
        start_page: int = 1,
        pages_to_fetch: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Retrieves chunks grouped by page sequentially instead of vector similarity.
        Useful for "page by page" instructions.
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, FieldCondition, MatchAny, Range

            if settings.QDRANT_URL == "local":
                client = QdrantClient(path="./qdrant_data")
            else:
                client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

            # Filter by documents and explicit page bounds
            page_filter = Filter(
                must=[
                    FieldCondition(key="document_id", match=MatchAny(any=document_ids)),
                    FieldCondition(key="page_number", range=Range(gte=start_page, lte=start_page + pages_to_fetch - 1))
                ]
            )

            # Perform a scroll to get points without vector matching
            records, _ = client.scroll(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                scroll_filter=page_filter,
                limit=100  # assuming chunks per 2 pages won't exceed 100
            )

            results = []
            for hit in records:
                results.append({
                    "id": hit.id,
                    "content": hit.payload.get("content", ""),
                    "page": hit.payload.get("page_number", 0),
                    "doc_id": hit.payload.get("document_id", ""),
                    "doc_name": hit.payload.get("document_name", ""),
                    "score": 1.0  # Sequential doesn't have similarity
                })
            
            # Group / sort by page explicitly
            results = sorted(results, key=lambda x: x["page"])
            return results

        except Exception as e:
            logger.error(f"Sequential search error: {e}")
            return []

    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using cross-encoder for better relevance.
        Uses sentence-transformers for semantic reranking.
        """
        if not results:
            return []

        try:
            from app.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()

            # Prepare pairs for scoring
            pairs = [
                [query, result["content"]]
                for result in results
            ]

            # Get scores
            scores = embedding_service.rerank_pairs(pairs)

            # Attach scores and sort
            for i, result in enumerate(results):
                result["rerank_score"] = scores[i]

            # Sort by rerank score and take top_k
            reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
            return reranked[:top_k]

        except ImportError as e:
            logger.warning(f"Cross-encoder not installed, skipping reranking: {e}")
            return results[:top_k]
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return results[:top_k]

    async def generate_response(
        self,
        query: str,
        documents: List[Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        mode: str = "NORMAL",
        user_id: str = None,
        db: Any = None
    ) -> Dict[str, Any]:
        """
        Main RAG pipeline: rewrite query, retrieve context, rerank, and generate response.
        If mode is NORMAL, bypasses RAG and acts as a standard conversational agent.
        """


        # Step 0: NORMAL Mode directly bypasses RAG
        if mode.upper() == "NORMAL":
            return await self.generate_without_context(query, mode=mode, conversation_history=conversation_history)

        # Step 1: Rewrite query using conversation context
        rewritten_query = await self._rewrite_query(query, conversation_history or [])

        # Step 2: Generate embedding for query
        query_embedding = await self._generate_embedding(rewritten_query)

        # Step 3: Search vector database
        document_ids = [doc.id for doc in documents]
        document_map = {doc.id: doc for doc in documents}

        if not document_ids:
            return await self.generate_without_context(query, mode=mode, conversation_history=conversation_history)

        SEQUENTIAL_KEYWORDS = [
            "page by page",
            "step by step",
            "from start",
            "from beginning",
            "go through"
        ]
        use_sequential = any(k in query.lower() for k in SEQUENTIAL_KEYWORDS)
        search_results = []
        if use_sequential:
            search_results = await self._search_sequential(document_ids, start_page=1, pages_to_fetch=2)
            reranked_results = search_results # Skip reranker for sequential
        else:
            search_results = await self._search_vectors(
                query_embedding,
                document_ids,
                top_k=settings.VECTOR_SEARCH_TOP_K
            )

        if not search_results:
            # No results from vector search, respond without context
            return await self.generate_without_context(query, mode=mode, conversation_history=conversation_history)

        # Step 4: Rerank results
        if not use_sequential:
            reranked_results = await self._rerank_results(
                rewritten_query,
                search_results,
                top_k=settings.RERANK_TOP_K
            )

        # Step 5: Confidence Threshold Block (Disabled to allow document answers)
        # We disabled the strict logger threshold because cross-encoder logits 
        # range arbitrarily (-10 to 10) causing artificial blocking.

        # Step 6: Build context from chunks
        context_chunks = []
        sources = []

        for result in reranked_results:
            context_chunks.append(f"[Page {result['page']}] {result['content']}")
            doc_obj = document_map.get(result["doc_id"])
            sources.append({
                "page": result["page"],
                "docId": result["doc_id"],
                "docName": result.get("doc_name", doc_obj.name if doc_obj else "Unknown")
            })

        context = "\n\n---\n\n".join(context_chunks)

        # Detect precise topic
        detected_topic = self.topic_service.detect_topic(query, [r["content"] for r in reranked_results])

        # Retrieve weak topics and evaluate previous answer for adaptive targeting
        weak_topics = []
        suggested_mode = None
        new_conf = None
        exam_state_prompt = ""
        suggest_text = ""
        
        session = _user_sessions.get(user_id, {"topics": [], "exam_history": []}) if user_id else None
        if session and detected_topic and detected_topic not in session["topics"]:
            session["topics"].append(detected_topic)
            if len(session["topics"]) > 5:
                session["topics"].pop(0)
        
        if db and user_id:
            suggested_mode = self.learning_state_service.get_suggested_mode(db, user_id, detected_topic)
            if suggested_mode:
                suggest_text = f"\n\nThe system recommends switching to [{suggested_mode}]. Integrate a smooth, natural-language invitation to switch to this mode at the end of your response."
            
            if mode.upper() in ["REVISION", "EXAM"]:
                weak_topics = self.learning_state_service.get_weak_topics(db, user_id, limit=3)
                
            if mode.upper() in ["TEACHER", "EXAM"] and conversation_history:
                last_msg = conversation_history[-1] if conversation_history else None
                eval_res = await self.evaluation_service.evaluate_answer(query, last_msg.get("content", ""), mode)
                new_conf = self.learning_state_service.update_confidence(db, user_id, detected_topic, eval_res["is_correct"])
                
                if mode.upper() == "EXAM" and session is not None:
                    session["exam_history"].append(eval_res["is_correct"])
                    if len(session["exam_history"]) > 3:
                        session["exam_history"].pop(0)
                        
                    history = session["exam_history"]
                    if len(history) == 3 and all(history):
                        exam_state_prompt = "\nDifficulty: increase (user passed last 3 questions)"
                    elif len(history) == 3 and not any(history):
                        exam_state_prompt = f"\nFocus Topic: {detected_topic}\nDifficulty: decrease (user failed last 3 questions)"
                    else:
                        exam_state_prompt = "\nDifficulty: maintain"

        if user_id:
            _user_sessions[user_id] = session

        weak_topics_text = f"\n\nUser's Weak Topics:\n{', '.join(weak_topics)}\n(Use weak topics only if they are relevant to the current question.)" if weak_topics else ""
        session_topics_text = f"\n\nSession Topics Studied:\n{', '.join(session['topics'])}" if session and session["topics"] else ""

        # Logging
        logger.info(f"[RAG] Mode: {mode} | Retrieval: {'Sequential' if use_sequential else 'Vector'} | Pages: {len(sources)} | Topic: {detected_topic} | Conf: {new_conf} | Diff: {exam_state_prompt.strip()} | Suggest: {suggested_mode}")

        # Step 7: Generate response with LLM
        system_prompt = get_prompt_for_mode(mode)
        if use_sequential:
            system_prompt += "\nStay within the scope of the document. You may simplify or rephrase, but do not introduce unrelated concepts."
        if exam_state_prompt:
            system_prompt += f"\n\n## Exam State Memory{exam_state_prompt}"
        if suggest_text:
            system_prompt += suggest_text
        system_prompt += session_topics_text

        user_prompt = f"""Context from documents:
{context}{weak_topics_text}

Question: {query}

Answer:"""

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

        return {
            "text": response.choices[0].message.content,
            "sources": sources,
            "topic": detected_topic,
            "suggest_mode": suggested_mode,
            "confidence_score": new_conf
        }

    async def generate_without_context(self, query: str, mode: str = "NORMAL", conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response when no document context is available.
        Includes a disclaimer about not using uploaded documents.
        """
        base_prompt = get_prompt_for_mode(mode)
        system_prompt = base_prompt + "\n\nIf the user asks an academic question, politely inform them that no documents are available and suggest they upload one to get started."

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content

    async def generate_response_stream(
        self,
        query: str,
        documents: List[Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        mode: str = "NORMAL",
        user_id: str = None,
        db: Any = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main RAG pipeline with streaming response.
        Yields SSE events for tokens as they are generated.
        Integrates learning state tracking and evaluation.
        If mode is NORMAL, bypasses RAG and streams as a standard conversational agent.
        """


        # Step 0: NORMAL Mode directly bypasses RAG
        if mode.upper() == "NORMAL":
            async for chunk in self.generate_without_context_stream(query, mode=mode, conversation_history=conversation_history):
                yield chunk
            return

        # Step 1: Rewrite query using conversation context
        rewritten_query = await self._rewrite_query(query, conversation_history or [])

        # Step 2: Generate embedding for query
        query_embedding = await self._generate_embedding(rewritten_query)

        # Step 3: Search vector database
        document_ids = [doc.id for doc in documents]
        document_map = {doc.id: doc for doc in documents}

        if not document_ids:
            async for chunk in self.generate_without_context_stream(query, mode=mode, conversation_history=conversation_history):
                yield chunk
            return

        SEQUENTIAL_KEYWORDS = [
            "page by page",
            "step by step",
            "from start",
            "from beginning",
            "go through"
        ]
        use_sequential = any(k in query.lower() for k in SEQUENTIAL_KEYWORDS)
        search_results = []
        if use_sequential:
            search_results = await self._search_sequential(document_ids, start_page=1, pages_to_fetch=2)
            reranked_results = search_results
        else:
            search_results = await self._search_vectors(
                query_embedding,
                document_ids,
                top_k=settings.VECTOR_SEARCH_TOP_K
            )

        if not search_results:
            # No results from vector search, stream response without context
            async for chunk in self.generate_without_context_stream(query, mode=mode, conversation_history=conversation_history):
                yield chunk
            return

        # Step 4: Rerank results
        if not use_sequential:
            reranked_results = await self._rerank_results(
                rewritten_query,
                search_results,
                top_k=settings.RERANK_TOP_K
            )

        # Step 5: Confidence Threshold Block (Disabled to allow document answers)
        # We disabled the strict logger threshold because cross-encoder logits 
        # range arbitrarily (-10 to 10) causing artificial blocking.

        # Step 6: Build context from chunks
        context_chunks = []
        sources = []

        for result in reranked_results:
            context_chunks.append(f"[Page {result['page']}] {result['content']}")
            doc_obj = document_map.get(result["doc_id"])
            sources.append({
                "page": result["page"],
                "docId": result["doc_id"],
                "docName": result.get("doc_name", doc_obj.name if doc_obj else "Unknown")
            })

        context = "\n\n---\n\n".join(context_chunks)

        # Detect precise topic
        detected_topic = self.topic_service.detect_topic(query, [r["content"] for r in reranked_results])
        yield {"type": "topic", "topic": detected_topic}

        # Check for mode switch suggestion based on learning state
        weak_topics = []
        suggested_mode = None
        new_conf = None
        exam_state_prompt = ""
        suggest_text = ""
        
        session = _user_sessions.get(user_id, {"topics": [], "exam_history": []}) if user_id else None
        if session and detected_topic and detected_topic not in session["topics"]:
            session["topics"].append(detected_topic)
            if len(session["topics"]) > 5:
                session["topics"].pop(0)

        if db and user_id:
            suggested_mode = self.learning_state_service.get_suggested_mode(db, user_id, detected_topic)
            if suggested_mode:
                suggest_text = f"\n\nThe system recommends switching to [{suggested_mode}]. Integrate a smooth, natural-language invitation to switch to this mode at the end of your response."
                yield {"type": "suggest_mode", "suggest_mode": suggested_mode}
                
            if mode.upper() in ["REVISION", "EXAM"]:
                weak_topics = self.learning_state_service.get_weak_topics(db, user_id, limit=3)

        # Evaluate answer if taking a test/teacher mode in a prior turn
        if db and user_id and mode in ["TEACHER", "EXAM"] and conversation_history:
            last_msg = conversation_history[-1] if conversation_history else None
            eval_res = await self.evaluation_service.evaluate_answer(query, last_msg.get("content", ""), mode)
            new_conf = self.learning_state_service.update_confidence(db, user_id, detected_topic, eval_res["is_correct"])
            yield {"type": "confidence_score", "confidence_score": new_conf}
            
            if mode.upper() == "EXAM" and session is not None:
                session["exam_history"].append(eval_res["is_correct"])
                if len(session["exam_history"]) > 3:
                    session["exam_history"].pop(0)
                    
                history = session["exam_history"]
                if len(history) == 3 and all(history):
                    exam_state_prompt = "\nDifficulty: increase (user passed last 3 questions)"
                elif len(history) == 3 and not any(history):
                    exam_state_prompt = f"\nFocus Topic: {detected_topic}\nDifficulty: decrease (user failed last 3 questions)"
                else:
                    exam_state_prompt = "\nDifficulty: maintain"

        if user_id:
            _user_sessions[user_id] = session
            
        session_topics_text = f"\n\nSession Topics Studied:\n{', '.join(session['topics'])}" if session and session["topics"] else ""

        # Logging
        logger.info(f"[RAG Stream] Mode: {mode} | Retrieval: {'Sequential' if use_sequential else 'Vector'} | Pages: {len(sources)} | Topic: {detected_topic} | Conf: {new_conf} | Diff: {exam_state_prompt.strip()} | Suggest: {suggested_mode}")

        # Yield sources first so frontend can display them immediately
        yield {
            "type": "sources",
            "sources": sources
        }

        # Step 7: Generate response with LLM streaming
        system_prompt = get_prompt_for_mode(mode)
        if use_sequential:
            system_prompt += "\nStay within the scope of the document. You may simplify or rephrase, but do not introduce unrelated concepts."
        if exam_state_prompt:
            system_prompt += f"\n\n## Exam State Memory{exam_state_prompt}"
        if suggest_text:
            system_prompt += suggest_text
        system_prompt += session_topics_text

        weak_topics_text = f"\n\nUser's Weak Topics:\n{', '.join(weak_topics)}\n(Use weak topics only if they are relevant to the current question.)" if weak_topics else ""

        user_prompt = f"""Context from documents:
{context}{weak_topics_text}

Question: {query}

Answer:"""

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "text",
                        "content": chunk.choices[0].delta.content
                    }
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "type": "text",
                "content": f"\n\n[Error: {str(e)}. Please check your GROQ_API_KEY in the .env file!]"
            }

        yield {"type": "done"}

    async def generate_without_context_stream(self, query: str, mode: str = "NORMAL", conversation_history: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming response when no document context is available.
        """
        yield {
            "type": "sources",
            "sources": []
        }

        base_prompt = get_prompt_for_mode(mode)
        system_prompt = base_prompt + "\n\nIf the user asks an academic question, politely inform them that no documents are available and suggest they upload one to get started."

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "text",
                        "content": chunk.choices[0].delta.content
                    }
        except Exception as e:
            logger.error(f"Stream error (no context): {e}")
            yield {
                "type": "text",
                "content": f"\n\n[Error: {str(e)}. Please check your GROQ_API_KEY in the .env file!]"
            }

        yield {"type": "done"}
