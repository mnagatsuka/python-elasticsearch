from typing import List, Optional, Dict, Any
from elasticsearch_dsl import Search, Q
from elasticsearch.exceptions import NotFoundError
from app.models.document import Article, User
from app.core.elasticsearch import get_elasticsearch_client
import logging

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document operations"""
    
    @staticmethod
    async def create_article(article_data: Dict[str, Any]) -> Article:
        """Create a new article"""
        try:
            article = Article(**article_data)
            article.save()
            logger.info(f"Created article with ID: {article.meta.id}")
            return article
        except Exception as e:
            logger.error(f"Failed to create article: {e}")
            raise
    
    @staticmethod
    async def get_article(article_id: str) -> Optional[Article]:
        """Get article by ID"""
        try:
            return Article.get(id=article_id)
        except NotFoundError:
            logger.warning(f"Article not found: {article_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get article {article_id}: {e}")
            raise
    
    @staticmethod
    async def search_articles(
        query: str = None,
        category: str = None,
        tags: List[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Article]:
        """Search articles with filters"""
        try:
            search = Search(index=Article._index._name)
            
            if query:
                search = search.query(
                    Q('multi_match', query=query, fields=['title^2', 'content'])
                )
            
            if category:
                search = search.filter('term', category=category)
            
            if tags:
                search = search.filter('terms', tags=tags)
            
            search = search[offset:offset + limit]
            
            response = search.execute()
            return [hit for hit in response.hits]
        
        except Exception as e:
            logger.error(f"Failed to search articles: {e}")
            raise
    
    @staticmethod
    async def update_article(article_id: str, update_data: Dict[str, Any]) -> Optional[Article]:
        """Update an article"""
        try:
            article = Article.get(id=article_id)
            for key, value in update_data.items():
                setattr(article, key, value)
            article.save()
            logger.info(f"Updated article with ID: {article_id}")
            return article
        except NotFoundError:
            logger.warning(f"Article not found for update: {article_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to update article {article_id}: {e}")
            raise
    
    @staticmethod
    async def delete_article(article_id: str) -> bool:
        """Delete an article"""
        try:
            article = Article.get(id=article_id)
            article.delete()
            logger.info(f"Deleted article with ID: {article_id}")
            return True
        except NotFoundError:
            logger.warning(f"Article not found for deletion: {article_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete article {article_id}: {e}")
            raise
    
    @staticmethod
    async def create_user(user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        try:
            user = User(**user_data)
            user.save()
            logger.info(f"Created user with ID: {user.meta.id}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    @staticmethod
    async def get_user(user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return User.get(id=user_id)
        except NotFoundError:
            logger.warning(f"User not found: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise