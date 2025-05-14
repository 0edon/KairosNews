import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from models.LexRank import degree_centrality_scores
import logging
from datetime import datetime as dt

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, embedding_model, summarization_model, nlp_model, db_service):
        self.embedding_model = embedding_model
        self.summarization_model = summarization_model
        self.nlp_model = nlp_model
        self.db_service = db_service
        logger.info("QueryProcessor initialized")

    async def process(
        self,
        query: str,
        topic: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # Date handling
            start_dt = self._parse_date(start_date) if start_date else None
            end_dt = self._parse_date(end_date) if end_date else None
            
            # Query processing
            query_embedding = self.embedding_model.encode(query).tolist()
            entities = self.nlp_model.extract_entities(query)
            print(f"Extracted entities: {entities}")
            
            # Database search
            articles = await self._execute_semantic_search(
                query_embedding,
                start_dt,
                end_dt,
                topic,
                entities
            )
            
            if not articles:
                return {"message": "No articles found", "articles": []}

            # Summary generation
            print("Starting summary generation")
            summary_data = self._generate_summary(articles)
            return {
                "summary": summary_data["summary"],
                "articles": articles,
                "entities": entities
            }

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def _parse_date(self, date_str: str) -> dt:
        """Safe date parsing with validation"""
        try:
            return dt.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Invalid date format: {date_str}")
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got {date_str}")

    def _extract_entities_safely(self, text: str) -> List[Tuple[str, str]]:
        """Robust entity extraction handling both strings and lists"""
        try:
            if isinstance(text, list):
                logger.warning("Received list input for entity extraction, joining to string")
                text = " ".join(text)
            return self.nlp_model.extract_entities(text)
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return []

    async def _execute_semantic_search(
        self,
        query_embedding: List[float],
        start_date: Optional[dt],
        end_date: Optional[dt],
        topic: Optional[str],
        entities: List[Tuple[str, str]]
    ) -> List[Dict[str, Any]]:
        """Execute search with proper error handling"""
        try:
            return await self.db_service.semantic_search(
                query_embedding=query_embedding,
                start_date=start_date,
                end_date=end_date,
                topic=topic,
                entities=entities
            )
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise

    def _generate_summary(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary from articles with fallback handling"""
        try:
            contents = [article["content"] for article in articles[:5]]
            sentences = []
            
            for content in contents:
                if content:
                    sentences.extend(self.nlp_model.tokenize_sentences(content))
            
            if not sentences:
                logger.warning("No sentences available for summarization")
                return {
                    "summary": "No content available for summarization",
                }
            
            print("Starting first summary generation")
            embeddings = self.embedding_model.encode(sentences)
            similarity_matrix = np.dot(embeddings, embeddings.T) / (np.linalg.norm(embeddings, axis=1, keepdims=True) * np.linalg.norm(embeddings, axis=1, keepdims=True).T)
            centrality_scores = degree_centrality_scores(similarity_matrix, threshold=0.1)
            
            top_indices = np.argsort(-centrality_scores)[:10]
            key_sentences = [sentences[idx].strip() for idx in top_indices]
            combined_text = ' '.join(key_sentences)
            
            print(f"First summary done with: {len(key_sentences)} sentences")

            return {
                "summary": self.summarization_model.summarize(combined_text),
            }

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {
                "summary": "Summary generation failed",
            }