import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class TopicService:
    """
    Topic Detection System for tracking the learning state per topic.
    Extracts topics from user queries and retrieved chunks.
    """

    def __init__(self):
        # Extendable knowledge base of topics mapping keywords to primary topics
        self.knowledge_base = {
            "math": ["algebra", "calculus", "geometry", "trigonometry", "equations", "functions", "derivative", "integral"],
            "biology": ["cell", "dna", "mitochondria", "respiration", "photosynthesis", "genetics", "evolution"],
            "chemistry": ["atom", "molecule", "reaction", "acid", "base", "periodic table", "moles", "bonding"],
            "physics": ["force", "motion", "energy", "thermodynamics", "quantum", "relativity", "kinematics", "gravity"],
            "history": ["war", "empire", "revolution", "dynasty", "treaty", "century", "civilization"],
            "computer_science": ["algorithm", "data structure", "database", "network", "programming", "variable", "loop"]
        }

    def detect_topic(self, query: str, retrieved_chunks: List[str] = None) -> str:
        """
        Detects the academic topic from the query and retrieved context chunks.
        Falls back to 'general' if not enough confidence.
        """
        text_corpus = query.lower()
        if retrieved_chunks:
            # Add a small sampling of chunks to the corpus to aid detection
            text_corpus += " " + " ".join([chunk.lower()[:300] for chunk in retrieved_chunks[:3]])

        topic_scores = {topic: 0 for topic in self.knowledge_base.keys()}

        # Simple keyword scoring mechanism
        for topic, keywords in self.knowledge_base.items():
            for keyword in keywords:
                # Use regex to find whole words only
                matches = re.findall(rf'\b{keyword}\b', text_corpus)
                topic_scores[topic] += len(matches)

        # Detect the topic with the highest score
        best_topic = max(topic_scores, key=topic_scores.get)

        if topic_scores[best_topic] > 0:
            logger.info(f"TopicService: Detected topic '{best_topic}' with score {topic_scores[best_topic]}.")
            return best_topic

        # Fallback noun extraction could be added here (e.g., using spaCy for Phase 2)
        # For now, return generic topic.
        logger.info("TopicService: No distinct topic detected, using 'general'.")
        return "general"

def get_topic_service() -> TopicService:
    return TopicService()
