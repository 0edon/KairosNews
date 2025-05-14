import os
from typing import List, Dict, Optional,Tuple
from datetime import datetime
import psycopg2
from psycopg2 import sql

class DatabaseService:
    def __init__(self):
        # Supabase Connection Parameters
        self.DB_HOST = os.getenv("SUPABASE_HOST", "aws-0-eu-west-3.pooler.supabase.com")
        self.DB_PORT = os.getenv("DB_PORT", "6543")
        self.DB_NAME = os.getenv("DB_NAME", "postgres")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")

    async def semantic_search(
        #Query parameters
        self,
        query_embedding: List[float],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        topic: Optional[str] = None,
        entities: Optional[List[Tuple[str,str]]] = None,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        
        # Entity log Checking
        print(f"Extracted entities2: {entities}")
        
        try:
            with psycopg2.connect(
                user=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                dbname=self.DB_NAME
            ) as conn:
                with conn.cursor() as cursor:
                    # Base query
                    base_query = sql.SQL('''
                        WITH filtered_articles AS (
                            SELECT article_id
                            FROM articles.articles
                            WHERE 1=1
                    ''')

                    # Add date range filter (if both start and end dates provided)
                    if start_date and end_date:
                        base_query = sql.SQL('{}{}').format(
                            base_query,
                            sql.SQL(' AND date BETWEEN {} AND {}').format(
                                sql.Literal(start_date),
                                sql.Literal(end_date)
                            )
                        )

                    # Add topic filter (if provided)
                    if topic:
                        base_query = sql.SQL('{}{}').format(
                            base_query,
                            sql.SQL(' AND topic = {}').format(sql.Literal(topic))
                        )

                    base_query = sql.SQL('{} {}').format(
                        base_query,
                        sql.SQL(')')
                    )

                    # Add entity filter (if entities exist)
                    if entities:
                        entity_conditions = sql.SQL(" OR ").join(
                            sql.SQL("""
                                (LOWER(UNACCENT(word)) = LOWER(UNACCENT({})) 
                                AND entity_group = {})
                            """).format(
                                sql.Literal(e[0]),  # Lowercase + unaccented entity text
                                sql.Literal(e[1])   # Original entity label (case-sensitive)
                            ) for e in entities
                        )
                        
                        # Final query with entity conditions and all filters
                        final_query = sql.SQL('''
                            {base_query},
                            target_articles AS (
                                SELECT DISTINCT article_id
                                FROM articles.ner
                                WHERE ({entity_conditions})
                                AND article_id IN (SELECT article_id FROM filtered_articles)
                            )
                            SELECT
                                a.content,
                                a.embedding <=> {embedding}::vector AS distance,
                                a.date,
                                a.topic,
                                a.url   
                            FROM articles.articles a
                            JOIN target_articles t ON a.article_id = t.article_id
                            ORDER BY distance
                            LIMIT {limit}
                        ''').format(
                            base_query=base_query,
                            entity_conditions=entity_conditions,
                            embedding=sql.Literal(query_embedding),
                            limit=sql.Literal(limit)
                        )

                    # Final query with all filters but no entities
                    else:
                        print("No articles found with entities...")
                        final_query = sql.SQL('''
                            {base_query}
                            SELECT
                                a.content,
                                a.embedding <=> {embedding}::vector AS distance,
                                a.date,
                                a.topic,
                                a.url
                            FROM articles.articles a
                            JOIN filtered_articles f ON a.article_id = f.article_id
                            ORDER BY distance
                            LIMIT {limit}
                        ''').format(
                            base_query=base_query,
                            embedding=sql.Literal(query_embedding),
                            limit=sql.Literal(limit)
                        )

                    cursor.execute(final_query)
                    articles = cursor.fetchall()

                    # Fallback: Retry with no filters if no results, only semantic search
                    if not articles:
                        print("No articles found with the filters applied. Trying fallback query...")
                        fallback_query = sql.SQL('''
                            SELECT
                                content,
                                embedding <=> {}::vector AS distance,
                                date,
                                topic,
                                url
                            FROM articles.articles
                            ORDER BY distance
                            LIMIT {limit}
                        ''').format(
                            sql.Literal(query_embedding),
                            limit=sql.Literal(limit)
                        )
                        cursor.execute(fallback_query)
                        articles = cursor.fetchall()

                    # Format results
                    formatted_results = [
                        {
                            "content": content,
                            "distance": distance,
                            "date": art_date,
                            "topic": art_topic,
                            "url": url,
                        }
                        for content, distance, art_date, art_topic,url in articles
                    ]

                    return formatted_results

        except Exception as e:
            print(f"Database query error: {e}")
            return []

    async def close(self):
        # No explicit close needed with context manager
        pass