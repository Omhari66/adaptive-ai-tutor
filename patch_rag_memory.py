import re

file_path = "e:/rag_based_AI/backend/app/services/rag_service.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# ADD SESSION STATE
if "_user_sessions = {}" not in content:
    content = re.sub(
        r"logger = logging.getLogger\(__name__\)",
        "logger = logging.getLogger(__name__)\n\n# Global session tracking\n_user_sessions = {}",
        content
    )

# DEFINE THE FUNCTION TO INJECT SESSION LOGIC
def patch_evaluation_block(block):
    # This block finds the detected_topic until the weak_topics_text
    
    pattern = r'(# Detect precise topic\s+detected_topic = self\.topic_service\.detect_topic\(query, \[r\["content"\] for r in reranked_results\]\).*?)(\s+# Logging|\s+# Step 7)'
    
    def replacer(match):
        original_chunk = match.group(1)
        
        # We rewrite this chunk manually
        # Note: the match might capture different amounts in generate_response vs stream depending on what lies after
        
        return original_chunk

# Wait, regex is a bit risky. I will just do exact substring replacements.

old_sync_block = """        # Detect precise topic
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
            system_prompt += f"\\n\\n## Exam State Memory{exam_state_prompt}\""""

new_sync_block = """        # Detect precise topic
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
                suggest_text = f"\\n\\nThe system recommends switching to [{suggested_mode}]. Integrate a smooth, natural-language invitation to switch to this mode at the end of your response."
            
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
                        exam_state_prompt = "\\nDifficulty: increase (user passed last 3 questions)"
                    elif len(history) == 3 and not any(history):
                        exam_state_prompt = f"\\nFocus Topic: {detected_topic}\\nDifficulty: decrease (user failed last 3 questions)"
                    else:
                        exam_state_prompt = "\\nDifficulty: maintain"

        if user_id:
            _user_sessions[user_id] = session

        weak_topics_text = f"\\n\\nUser's Weak Topics:\\n{', '.join(weak_topics)}\\n(Use weak topics only if they are relevant to the current question.)" if weak_topics else ""
        session_topics_text = f"\\n\\nSession Topics Studied:\\n{', '.join(session['topics'])}" if session and session["topics"] else ""

        # Logging
        logger.info(f"[RAG] Mode: {mode} | Retrieval: {'Sequential' if use_sequential else 'Vector'} | Pages: {len(sources)} | Topic: {detected_topic} | Conf: {new_conf} | Diff: {exam_state_prompt.strip()} | Suggest: {suggested_mode}")

        # Step 7: Generate response with LLM
        system_prompt = get_prompt_for_mode(mode)
        if use_sequential:
            system_prompt += "\\nStay within the scope of the document. You may simplify or rephrase, but do not introduce unrelated concepts."
        if exam_state_prompt:
            system_prompt += f"\\n\\n## Exam State Memory{exam_state_prompt}"
        if suggest_text:
            system_prompt += suggest_text
        system_prompt += session_topics_text"""

old_stream_block = """        # Detect precise topic
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
            system_prompt += f"\\n\\n## Exam State Memory{exam_state_prompt}\""""

new_stream_block = """        # Detect precise topic
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
                suggest_text = f"\\n\\nThe system recommends switching to [{suggested_mode}]. Integrate a smooth, natural-language invitation to switch to this mode at the end of your response."
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
                    exam_state_prompt = "\\nDifficulty: increase (user passed last 3 questions)"
                elif len(history) == 3 and not any(history):
                    exam_state_prompt = f"\\nFocus Topic: {detected_topic}\\nDifficulty: decrease (user failed last 3 questions)"
                else:
                    exam_state_prompt = "\\nDifficulty: maintain"

        if user_id:
            _user_sessions[user_id] = session
            
        session_topics_text = f"\\n\\nSession Topics Studied:\\n{', '.join(session['topics'])}" if session and session["topics"] else ""

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
            system_prompt += "\\nStay within the scope of the document. You may simplify or rephrase, but do not introduce unrelated concepts."
        if exam_state_prompt:
            system_prompt += f"\\n\\n## Exam State Memory{exam_state_prompt}"
        if suggest_text:
            system_prompt += suggest_text
        system_prompt += session_topics_text"""

if old_sync_block in content:
    content = content.replace(old_sync_block, new_sync_block)
    print("Replaced sync block.")
else:
    print("Failed to find sync block.")

if old_stream_block in content:
    content = content.replace(old_stream_block, new_stream_block)
    print("Replaced stream block.")
else:
    print("Failed to find stream block.")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
