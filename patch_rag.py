import re

with open("e:/rag_based_AI/backend/app/services/rag_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# REPLACEMENT 1 for generate_response
old_block_1 = """        # Retrieve weak topics for adaptive targeting
        weak_topics = []
        if db and user_id and mode.upper() in ["REVISION", "EXAM"]:
            weak_topics = self.learning_state_service.get_weak_topics(db, user_id, limit=3)

        weak_topics_text = f"\\n\\nUser's Weak Topics:\\n{', '.join(weak_topics)}\\n(Prioritize these concepts if relevant to the context.)" if weak_topics else ""

        # Step 7: Generate response with LLM
        system_prompt = get_prompt_for_mode(mode)

        user_prompt = f\"\"\"Context from documents:
{context}{weak_topics_text}

Question: {query}

Answer:\"\"\"

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

        # Detect precise topic
        detected_topic = self.topic_service.detect_topic(query, [r["content"] for r in reranked_results])
        
        suggested_mode = None
        new_conf = None
        if db and user_id:
            suggested_mode = self.learning_state_service.get_suggested_mode(db, user_id, detected_topic)
            if mode in ["TEACHER", "EXAM"] and conversation_history:
                last_msg = conversation_history[-1] if conversation_history else None
                eval_res = await self.evaluation_service.evaluate_answer(query, last_msg.get("content", ""), mode)
                new_conf = self.learning_state_service.update_confidence(db, user_id, detected_topic, eval_res["is_correct"])

        return {
            "text": response.choices[0].message.content,
            "sources": sources,
            "topic": detected_topic,
            "suggest_mode": suggested_mode,
            "confidence_score": new_conf
        }"""

new_block_1 = """        # Detect precise topic
        detected_topic = self.topic_service.detect_topic(query, [r["content"] for r in reranked_results])

        # Retrieve weak topics and evaluate previous answer for adaptive targeting
        weak_topics = []
        suggested_mode = None
        new_conf = None
        exam_state_prompt = ""
        
        if db and user_id:
            suggested_mode = self.learning_state_service.get_suggested_mode(db, user_id, detected_topic)
            
            if mode.upper() in ["REVISION", "EXAM"]:
                weak_topics = self.learning_state_service.get_weak_topics(db, user_id, limit=3)
                
            if mode.upper() in ["TEACHER", "EXAM"] and conversation_history:
                last_msg = conversation_history[-1] if conversation_history else None
                eval_res = await self.evaluation_service.evaluate_answer(query, last_msg.get("content", ""), mode)
                new_conf = self.learning_state_service.update_confidence(db, user_id, detected_topic, eval_res["is_correct"])
                
                if mode.upper() == "EXAM":
                    if not eval_res["is_correct"]:
                        exam_state_prompt = f"\\nFocus Topic: {detected_topic}\\nDifficulty: easy (user failed previous question)"
                    else:
                        exam_state_prompt = f"\\nDifficulty: medium/hard (user passed previous question)"

        weak_topics_text = f"\\n\\nUser's Weak Topics:\\n{', '.join(weak_topics)}\\n(Use weak topics only if they are relevant to the current question.)" if weak_topics else ""

        # Logging
        logger.info(f"[RAG] Mode: {mode} | Retrieval: {'Sequential' if use_sequential else 'Vector'} | Pages: {len(sources)} | Topic: {detected_topic} | Conf: {new_conf}")

        # Step 7: Generate response with LLM
        system_prompt = get_prompt_for_mode(mode)
        if use_sequential:
            system_prompt += "\\nStay within the scope of the document. You may simplify or rephrase, but do not introduce unrelated concepts."
        if exam_state_prompt:
            system_prompt += f"\\n\\n## Exam State Memory{exam_state_prompt}"

        user_prompt = f\"\"\"Context from documents:
{context}{weak_topics_text}

Question: {query}

Answer:\"\"\"

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
        }"""

if old_block_1 in content:
    content = content.replace(old_block_1, new_block_1)
    print("Replaced chunk 1 successfully.")
else:
    print("Failed to find chunk 1.")


# REPLACEMENT 2 for generate_response_stream
old_block_2 = """        # Detect precise topic
        detected_topic = self.topic_service.detect_topic(query, [r["content"] for r in reranked_results])
        yield {"type": "topic", "topic": detected_topic}

        # Check for mode switch suggestion based on learning state
        suggested_mode = None
        new_conf = None
        if db and user_id:
            suggested_mode = self.learning_state_service.get_suggested_mode(db, user_id, detected_topic)
            if suggested_mode:
                yield {"type": "suggest_mode", "suggest_mode": suggested_mode}

        # Evaluate answer if taking a test/teacher mode in a prior turn
        if db and user_id and mode in ["TEACHER", "EXAM"] and conversation_history:
            # Did they answer a previous question?
            last_msg = conversation_history[-1] if conversation_history else None
            # If the last message was a question from the tutor (which is likely in these modes)
            # We would evaluate user's new query as the answer.
            # Realistically we should use the content from LLM history.
            eval_res = await self.evaluation_service.evaluate_answer(query, last_msg.get("content", ""), mode)
            new_conf = self.learning_state_service.update_confidence(db, user_id, detected_topic, eval_res["is_correct"])
            yield {"type": "confidence_score", "confidence_score": new_conf}

        # Yield sources first so frontend can display them immediately
        yield {
            "type": "sources",
            "sources": sources
        }

        # Step 7: Generate response with LLM streaming
        system_prompt = get_prompt_for_mode(mode)

        # Retrieve weak topics for adaptive targeting
        weak_topics = []
        if db and user_id and mode.upper() in ["REVISION", "EXAM"]:
            weak_topics = self.learning_state_service.get_weak_topics(db, user_id, limit=3)

        weak_topics_text = f"\\n\\nUser's Weak Topics:\\n{', '.join(weak_topics)}\\n(Prioritize these concepts if relevant to the context.)" if weak_topics else ""

        user_prompt = f\"\"\"Context from documents:
{context}{weak_topics_text}

Question: {query}

Answer:\"\"\"

        messages = [{"role": "system", "content": system_prompt}]"""

new_block_2 = """        # Detect precise topic
        detected_topic = self.topic_service.detect_topic(query, [r["content"] for r in reranked_results])
        yield {"type": "topic", "topic": detected_topic}

        # Check for mode switch suggestion based on learning state
        weak_topics = []
        suggested_mode = None
        new_conf = None
        exam_state_prompt = ""
        
        if db and user_id:
            suggested_mode = self.learning_state_service.get_suggested_mode(db, user_id, detected_topic)
            if suggested_mode:
                yield {"type": "suggest_mode", "suggest_mode": suggested_mode}
                
            if mode.upper() in ["REVISION", "EXAM"]:
                weak_topics = self.learning_state_service.get_weak_topics(db, user_id, limit=3)

        # Evaluate answer if taking a test/teacher mode in a prior turn
        if db and user_id and mode in ["TEACHER", "EXAM"] and conversation_history:
            last_msg = conversation_history[-1] if conversation_history else None
            eval_res = await self.evaluation_service.evaluate_answer(query, last_msg.get("content", ""), mode)
            new_conf = self.learning_state_service.update_confidence(db, user_id, detected_topic, eval_res["is_correct"])
            yield {"type": "confidence_score", "confidence_score": new_conf}
            
            if mode.upper() == "EXAM":
                if not eval_res["is_correct"]:
                    exam_state_prompt = f"\\nFocus Topic: {detected_topic}\\nDifficulty: easy (user failed previous question)"
                else:
                    exam_state_prompt = f"\\nDifficulty: medium/hard (user passed previous question)"
                    
        # Logging
        logger.info(f"[RAG Stream] Mode: {mode} | Retrieval: {'Sequential' if use_sequential else 'Vector'} | Pages: {len(sources)} | Topic: {detected_topic} | Conf: {new_conf}")

        # Yield sources first so frontend can display them immediately
        yield {
            "type": "sources",
            "sources": sources
        }

        # Step 7: Generate response with LLM streaming
        system_prompt = get_prompt_for_mode(mode)
        if use_sequential:
            system_prompt += "\\nStay within the scope of the document. You may simplify or rephrase, but do not introduce unrelated concepts."
        if exam_state_prompt:
            system_prompt += f"\\n\\n## Exam State Memory{exam_state_prompt}"

        weak_topics_text = f"\\n\\nUser's Weak Topics:\\n{', '.join(weak_topics)}\\n(Use weak topics only if they are relevant to the current question.)" if weak_topics else ""

        user_prompt = f\"\"\"Context from documents:
{context}{weak_topics_text}

Question: {query}

Answer:\"\"\"

        messages = [{"role": "system", "content": system_prompt}]"""

if old_block_2 in content:
    content = content.replace(old_block_2, new_block_2)
    print("Replaced chunk 2 successfully.")
else:
    print("Failed to find chunk 2.")

with open("e:/rag_based_AI/backend/app/services/rag_service.py", "w", encoding="utf-8") as f:
    f.write(content)
