from datetime import datetime
from elasticsearch_dsl import Document, Text, Keyword, Date, Integer, Float
from app.core.config import settings


class BaseDocument(Document):
    """Base document class with common fields"""
    created_at = Date()
    updated_at = Date()
    
    class Index:
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
    
    def save(self, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
        return super().save(**kwargs)


class Article(BaseDocument):
    """Article document model"""
    title = Text(analyzer='standard')
    content = Text(analyzer='standard')
    author = Keyword()
    category = Keyword()
    tags = Keyword(multi=True)
    views = Integer()
    rating = Float()
    
    class Index:
        name = f"{settings.elasticsearch_index_prefix}_articles"
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }


class User(BaseDocument):
    """User document model"""
    username = Keyword()
    email = Keyword()
    full_name = Text()
    bio = Text()
    is_active = Keyword()
    
    class Index:
        name = f"{settings.elasticsearch_index_prefix}_users"
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }