# Document Relationships

Managing complex data relationships in Elasticsearch using FastAPI with elasticsearch-dsl for efficient document modeling and cross-document queries.

## Table of Contents
- [Relationship Types Overview](#relationship-types-overview)
- [Parent-Child Relationships](#parent-child-relationships)
- [Reference-Based Relationships](#reference-based-relationships)
- [Nested Document Patterns](#nested-document-patterns)
- [Join Field Usage](#join-field-usage)
- [Service Layer Management](#service-layer-management)
- [Cross-Document Queries](#cross-document-queries)
- [Performance Considerations](#performance-considerations)
- [Next Steps](#next-steps)

## Relationship Types Overview

### Understanding Elasticsearch Relationships
```python
from typing import Optional, List, Dict, Any, Union
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Integer, Float, Date, Join, Nested, Object
from elasticsearch_dsl.connections import connections
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

# Relationship types in Elasticsearch
class RelationshipType:
    """Types of relationships available in Elasticsearch."""
    
    # 1. Object type - flattened structure
    OBJECT = "object"
    
    # 2. Nested type - separate documents in same index
    NESTED = "nested"
    
    # 3. Parent-child - separate documents with join field
    PARENT_CHILD = "parent_child"
    
    # 4. Reference-based - document IDs as references
    REFERENCE = "reference"
    
    # 5. Denormalized - duplicated data across documents
    DENORMALIZED = "denormalized"

class RelationshipChoice:
    """Guidelines for choosing relationship types."""
    
    @staticmethod
    def get_recommendation(
        relationship_type: str,
        query_patterns: List[str],
        update_frequency: str,
        data_volume: str
    ) -> Dict[str, str]:
        """Get relationship type recommendation."""
        
        recommendations = {
            "one_to_few": {
                "low_updates": "OBJECT or NESTED",
                "high_updates": "REFERENCE",
                "reason": "Simple structure for small collections"
            },
            "one_to_many": {
                "read_heavy": "NESTED or DENORMALIZED",
                "write_heavy": "REFERENCE or PARENT_CHILD",
                "reason": "Balance between query performance and update cost"
            },
            "many_to_many": {
                "any": "REFERENCE",
                "reason": "Avoid data duplication and maintain consistency"
            }
        }
        
        return recommendations.get(relationship_type, {
            "recommendation": "REFERENCE",
            "reason": "Most flexible for complex relationships"
        })
```

### Relationship Performance Matrix
```python
class RelationshipPerformanceMatrix:
    """Performance characteristics of different relationship types."""
    
    @staticmethod
    def get_performance_matrix() -> Dict[str, Dict[str, str]]:
        """Get performance matrix for relationship types."""
        return {
            "object": {
                "query_speed": "FASTEST",
                "update_speed": "FAST",
                "storage": "EFFICIENT",
                "flexibility": "LOW",
                "best_for": "Simple one-to-few relationships"
            },
            "nested": {
                "query_speed": "FAST",
                "update_speed": "MEDIUM",
                "storage": "MEDIUM",
                "flexibility": "MEDIUM",
                "best_for": "One-to-many with complex queries"
            },
            "parent_child": {
                "query_speed": "MEDIUM",
                "update_speed": "FAST",
                "storage": "EFFICIENT",
                "flexibility": "HIGH",
                "best_for": "Frequent updates to child documents"
            },
            "reference": {
                "query_speed": "SLOW",
                "update_speed": "FAST",
                "storage": "VERY_EFFICIENT",
                "flexibility": "HIGHEST",
                "best_for": "Complex many-to-many relationships"
            },
            "denormalized": {
                "query_speed": "FASTEST",
                "update_speed": "SLOWEST",
                "storage": "INEFFICIENT",
                "flexibility": "LOW",
                "best_for": "Read-heavy workloads with rare updates"
            }
        }
```

## Parent-Child Relationships

### Basic Parent-Child Setup
```python
from elasticsearch_dsl import Join

class BlogPost(AsyncDocument):
    """Blog post parent document."""
    
    title = Text(analyzer='standard')
    content = Text(analyzer='standard')
    author = Keyword()
    published_date = Date()
    
    # Join field for parent-child relationship
    blog_join = Join(relations={'post': 'comment'})
    
    class Index:
        name = 'blog'
        settings = {
            'number_of_shards': 1,  # Required for parent-child
            'number_of_replicas': 0
        }

class Comment(AsyncDocument):
    """Comment child document."""
    
    content = Text(analyzer='standard')
    author_name = Keyword()
    author_email = Keyword()
    created_date = Date()
    rating = Integer(min_value=1, max_value=5)
    
    # Join field reference
    blog_join = Join(relations={'post': 'comment'})
    
    class Index:
        name = 'blog'  # Same index as parent

# Pydantic models for API
class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    author: str = Field(..., min_length=1, max_length=100)

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    author_name: str = Field(..., min_length=1, max_length=100)
    author_email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    rating: int = Field(..., ge=1, le=5)

class CommentResponse(BaseModel):
    id: str
    content: str
    author_name: str
    rating: int
    created_date: datetime
    
    @classmethod
    def from_elasticsearch(cls, hit):
        return cls(
            id=hit.meta.id,
            content=hit.content,
            author_name=hit.author_name,
            rating=hit.rating,
            created_date=hit.created_date
        )

class BlogPostResponse(BaseModel):
    id: str
    title: str
    content: str
    author: str
    published_date: datetime
    comment_count: int = 0
    comments: List[CommentResponse] = []
    
    @classmethod
    def from_elasticsearch(cls, hit, comments=None):
        return cls(
            id=hit.meta.id,
            title=hit.title,
            content=hit.content,
            author=hit.author,
            published_date=hit.published_date,
            comment_count=len(comments) if comments else 0,
            comments=comments or []
        )
```

### Parent-Child Service Implementation
```python
from elasticsearch_dsl import AsyncSearch, Q
from elasticsearch.exceptions import NotFoundError

class BlogService:
    """Service for managing blog posts and comments."""
    
    @staticmethod
    async def create_blog_post(post_data: BlogPostCreate) -> str:
        """Create a new blog post."""
        try:
            post = BlogPost(
                title=post_data.title,
                content=post_data.content,
                author=post_data.author,
                published_date=datetime.utcnow(),
                blog_join={'name': 'post'}  # Mark as parent
            )
            
            await post.save()
            return post.meta.id
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")
    
    @staticmethod
    async def add_comment(post_id: str, comment_data: CommentCreate) -> str:
        """Add comment to blog post."""
        try:
            # Verify parent post exists
            try:
                post = await BlogPost.get(post_id)
            except NotFoundError:
                raise HTTPException(status_code=404, detail="Blog post not found")
            
            comment = Comment(
                content=comment_data.content,
                author_name=comment_data.author_name,
                author_email=comment_data.author_email,
                rating=comment_data.rating,
                created_date=datetime.utcnow(),
                blog_join={
                    'name': 'comment',
                    'parent': post_id  # Reference to parent
                }
            )
            
            # Child documents must be indexed with routing
            await comment.save(routing=post_id)
            return comment.meta.id
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")
    
    @staticmethod
    async def get_post_with_comments(post_id: str) -> BlogPostResponse:
        """Get blog post with all comments."""
        try:
            # Get parent document
            try:
                post = await BlogPost.get(post_id)
            except NotFoundError:
                raise HTTPException(status_code=404, detail="Blog post not found")
            
            # Query for child comments
            search = AsyncSearch(index='blog')
            search = search.filter('parent_id', type='comment', id=post_id)
            search = search.sort('created_date')
            
            comments_response = await search.execute()
            comments = [
                CommentResponse.from_elasticsearch(hit)
                for hit in comments_response.hits
            ]
            
            return BlogPostResponse.from_elasticsearch(post, comments)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get post: {str(e)}")
    
    @staticmethod
    async def get_posts_with_comment_stats() -> List[Dict[str, Any]]:
        """Get all posts with comment statistics."""
        try:
            search = AsyncSearch(index='blog')
            search = search.filter('term', **{'blog_join.name': 'post'})
            
            # Add aggregation for comment counts
            search.aggs.bucket('comments', 'children', type='comment').metric(
                'avg_rating', 'avg', field='rating'
            )
            
            response = await search.execute()
            
            posts = []
            for hit in response.hits:
                post_data = hit.to_dict()
                post_data['id'] = hit.meta.id
                
                # Get comment statistics from aggregations
                if hasattr(response, 'aggregations') and 'comments' in response.aggregations:
                    comment_stats = response.aggregations.comments
                    post_data['comment_count'] = comment_stats.doc_count
                    post_data['avg_rating'] = comment_stats.avg_rating.value if comment_stats.avg_rating.value else 0
                else:
                    post_data['comment_count'] = 0
                    post_data['avg_rating'] = 0
                
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get posts: {str(e)}")
```

## Reference-Based Relationships

### Reference Model Design
```python
class User(AsyncDocument):
    """User document with reference-based relationships."""
    
    username = Keyword()
    email = Keyword()
    full_name = Text()
    bio = Text()
    created_date = Date()
    
    class Index:
        name = 'users'

class Article(AsyncDocument):
    """Article document with user reference."""
    
    title = Text(analyzer='standard')
    content = Text(analyzer='standard')
    summary = Text()
    
    # Reference to user document
    author_id = Keyword()  # Reference to User._id
    
    # Denormalized fields for performance
    author_username = Keyword()  # Cached from User
    author_name = Text()  # Cached from User
    
    # Category references
    category_ids = Keyword()  # Multiple category references
    tag_ids = Keyword()  # Multiple tag references
    
    published_date = Date()
    view_count = Integer()
    like_count = Integer()
    
    class Index:
        name = 'articles'

class Category(AsyncDocument):
    """Category document."""
    
    name = Keyword()
    description = Text()
    slug = Keyword()
    parent_category_id = Keyword()  # Self-reference for hierarchy
    
    class Index:
        name = 'categories'

class Tag(AsyncDocument):
    """Tag document."""
    
    name = Keyword()
    description = Text()
    color = Keyword()
    
    class Index:
        name = 'tags'

# API models
class ArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=50)
    summary: str = Field(..., min_length=10, max_length=500)
    category_ids: List[str] = Field(..., min_items=1, max_items=5)
    tag_ids: List[str] = Field(default=[], max_items=10)

class ArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    summary: str
    author: Dict[str, str]  # {id, username, name}
    categories: List[Dict[str, str]]  # [{id, name, slug}]
    tags: List[Dict[str, str]]  # [{id, name, color}]
    published_date: datetime
    view_count: int
    like_count: int
```

### Reference-Based Service
```python
from typing import Dict, Set

class ArticleService:
    """Service for managing articles with references."""
    
    @staticmethod
    async def create_article(
        article_data: ArticleCreateRequest,
        author_id: str
    ) -> str:
        """Create article with reference validation."""
        try:
            # Validate author exists
            try:
                author = await User.get(author_id)
            except NotFoundError:
                raise HTTPException(status_code=404, detail="Author not found")
            
            # Validate categories exist
            category_docs = await ArticleService._get_documents_by_ids(
                Category, article_data.category_ids
            )
            if len(category_docs) != len(article_data.category_ids):
                raise HTTPException(status_code=400, detail="Some categories not found")
            
            # Validate tags exist
            tag_docs = []
            if article_data.tag_ids:
                tag_docs = await ArticleService._get_documents_by_ids(
                    Tag, article_data.tag_ids
                )
                if len(tag_docs) != len(article_data.tag_ids):
                    raise HTTPException(status_code=400, detail="Some tags not found")
            
            # Create article with references and denormalized data
            article = Article(
                title=article_data.title,
                content=article_data.content,
                summary=article_data.summary,
                
                # References
                author_id=author_id,
                category_ids=article_data.category_ids,
                tag_ids=article_data.tag_ids,
                
                # Denormalized author data
                author_username=author.username,
                author_name=author.full_name,
                
                published_date=datetime.utcnow(),
                view_count=0,
                like_count=0
            )
            
            await article.save()
            return article.meta.id
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create article: {str(e)}")
    
    @staticmethod
    async def get_article_with_references(article_id: str) -> ArticleResponse:
        """Get article with resolved references."""
        try:
            # Get article
            try:
                article = await Article.get(article_id)
            except NotFoundError:
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Resolve references concurrently
            author_task = ArticleService._get_document_by_id(User, article.author_id)
            categories_task = ArticleService._get_documents_by_ids(Category, article.category_ids)
            tags_task = ArticleService._get_documents_by_ids(Tag, article.tag_ids)
            
            author, categories, tags = await asyncio.gather(
                author_task, categories_task, tags_task
            )
            
            # Build response
            return ArticleResponse(
                id=article.meta.id,
                title=article.title,
                content=article.content,
                summary=article.summary,
                
                author={
                    'id': author.meta.id,
                    'username': author.username,
                    'name': author.full_name
                },
                
                categories=[
                    {
                        'id': cat.meta.id,
                        'name': cat.name,
                        'slug': cat.slug
                    }
                    for cat in categories
                ],
                
                tags=[
                    {
                        'id': tag.meta.id,
                        'name': tag.name,
                        'color': tag.color
                    }
                    for tag in tags
                ],
                
                published_date=article.published_date,
                view_count=article.view_count,
                like_count=article.like_count
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}")
    
    @staticmethod
    async def _get_document_by_id(doc_class, doc_id: str):
        """Get single document by ID."""
        try:
            return await doc_class.get(doc_id)
        except NotFoundError:
            return None
    
    @staticmethod
    async def _get_documents_by_ids(doc_class, doc_ids: List[str]) -> List:
        """Get multiple documents by IDs."""
        if not doc_ids:
            return []
        
        search = AsyncSearch(index=doc_class._get_index())
        search = search.filter('terms', _id=doc_ids)
        search = search.extra(size=len(doc_ids))
        
        response = await search.execute()
        return list(response.hits)
    
    @staticmethod
    async def update_author_references(user_id: str, updated_data: Dict[str, str]):
        """Update denormalized author data across articles."""
        try:
            # Search for articles by this author
            search = AsyncSearch(index='articles')
            search = search.filter('term', author_id=user_id)
            search = search.extra(size=1000)  # Adjust based on expected volume
            
            response = await search.execute()
            
            # Bulk update denormalized data
            updates = []
            for hit in response.hits:
                article = await Article.get(hit.meta.id)
                
                if 'username' in updated_data:
                    article.author_username = updated_data['username']
                if 'full_name' in updated_data:
                    article.author_name = updated_data['full_name']
                
                updates.append(article.save())
            
            if updates:
                await asyncio.gather(*updates)
            
            return len(updates)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update author references: {str(e)}"
            )
```

## Nested Document Patterns

### Nested Document Models
```python
from elasticsearch_dsl import Nested, Object

class Address(Object):
    """Address as nested object."""
    
    street = Text()
    city = Keyword()
    state = Keyword()
    postal_code = Keyword()
    country = Keyword()
    is_primary = Boolean()

class ContactInfo(Object):
    """Contact information as nested object."""
    
    type = Keyword()  # phone, email, social
    value = Keyword()
    is_verified = Boolean()

class Company(AsyncDocument):
    """Company with nested address and contact information."""
    
    name = Text(analyzer='standard')
    description = Text()
    industry = Keyword()
    size = Integer()
    
    # Nested documents
    addresses = Nested(Address)
    contacts = Nested(ContactInfo)
    
    # Nested employee data
    employees = Nested(properties={
        'name': Text(),
        'title': Keyword(),
        'department': Keyword(),
        'email': Keyword(),
        'hire_date': Date(),
        'salary_range': Keyword(),
        'skills': Keyword()
    })
    
    founded_date = Date()
    revenue = Float()
    
    class Index:
        name = 'companies'

# API models for nested data
class AddressData(BaseModel):
    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)
    is_primary: bool = False

class ContactData(BaseModel):
    type: str = Field(..., regex=r'^(phone|email|social)$')
    value: str = Field(..., min_length=1, max_length=200)
    is_verified: bool = False

class EmployeeData(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    hire_date: datetime
    salary_range: str = Field(..., regex=r'^(entry|mid|senior|executive)$')
    skills: List[str] = Field(default=[], max_items=20)

class CompanyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    industry: str = Field(..., min_length=1, max_length=100)
    size: int = Field(..., gt=0)
    addresses: List[AddressData] = Field(..., min_items=1, max_items=5)
    contacts: List[ContactData] = Field(..., min_items=1, max_items=10)
    employees: List[EmployeeData] = Field(default=[], max_items=1000)
    founded_date: datetime
    revenue: Optional[float] = Field(None, ge=0)
```

### Nested Document Service
```python
class CompanyService:
    """Service for managing companies with nested documents."""
    
    @staticmethod
    async def create_company(company_data: CompanyCreateRequest) -> str:
        """Create company with nested documents."""
        try:
            # Validate addresses have exactly one primary
            primary_addresses = [addr for addr in company_data.addresses if addr.is_primary]
            if len(primary_addresses) != 1:
                raise HTTPException(
                    status_code=400,
                    detail="Exactly one address must be marked as primary"
                )
            
            # Convert Pydantic models to dictionaries for Elasticsearch
            addresses_data = [addr.dict() for addr in company_data.addresses]
            contacts_data = [contact.dict() for contact in company_data.contacts]
            employees_data = [emp.dict() for emp in company_data.employees]
            
            company = Company(
                name=company_data.name,
                description=company_data.description,
                industry=company_data.industry,
                size=company_data.size,
                addresses=addresses_data,
                contacts=contacts_data,
                employees=employees_data,
                founded_date=company_data.founded_date,
                revenue=company_data.revenue
            )
            
            await company.save()
            return company.meta.id
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")
    
    @staticmethod
    async def search_companies_by_employee_skills(skills: List[str]) -> List[Dict[str, Any]]:
        """Search companies by employee skills using nested queries."""
        try:
            search = AsyncSearch(index='companies')
            
            # Nested query for employee skills
            nested_query = Q('nested',
                path='employees',
                query=Q('terms', **{'employees.skills': skills})
            )
            
            search = search.query(nested_query)
            
            # Add nested aggregation to get skill counts
            search.aggs.bucket('employee_skills', 'nested', path='employees').bucket(
                'skills', 'terms', field='employees.skills', size=50
            )
            
            response = await search.execute()
            
            companies = []
            for hit in response.hits:
                company_data = hit.to_dict()
                company_data['id'] = hit.meta.id
                
                # Filter employees with matching skills
                matching_employees = []
                for employee in company_data.get('employees', []):
                    if any(skill in employee.get('skills', []) for skill in skills):
                        matching_employees.append(employee)
                
                company_data['matching_employees'] = matching_employees
                company_data['matching_employee_count'] = len(matching_employees)
                
                companies.append(company_data)
            
            return companies
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search companies: {str(e)}"
            )
    
    @staticmethod
    async def add_employee_to_company(
        company_id: str,
        employee_data: EmployeeData
    ) -> bool:
        """Add employee to existing company."""
        try:
            # Get company
            try:
                company = await Company.get(company_id)
            except NotFoundError:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Check if employee email already exists
            existing_emails = [emp.get('email') for emp in company.employees]
            if employee_data.email in existing_emails:
                raise HTTPException(
                    status_code=400,
                    detail="Employee with this email already exists"
                )
            
            # Add new employee
            company.employees.append(employee_data.dict())
            await company.save()
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add employee: {str(e)}"
            )
    
    @staticmethod
    async def update_employee_in_company(
        company_id: str,
        employee_email: str,
        updated_data: Dict[str, Any]
    ) -> bool:
        """Update specific employee in company."""
        try:
            # Get company
            try:
                company = await Company.get(company_id)
            except NotFoundError:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Find and update employee
            employee_updated = False
            for i, employee in enumerate(company.employees):
                if employee.get('email') == employee_email:
                    # Update allowed fields
                    allowed_fields = {'title', 'department', 'salary_range', 'skills'}
                    for field, value in updated_data.items():
                        if field in allowed_fields:
                            company.employees[i][field] = value
                    
                    employee_updated = True
                    break
            
            if not employee_updated:
                raise HTTPException(status_code=404, detail="Employee not found")
            
            await company.save()
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update employee: {str(e)}"
            )
```

## Join Field Usage

### Advanced Join Patterns
```python
class ContentDocument(AsyncDocument):
    """Multi-level parent-child with join fields."""
    
    title = Text()
    content = Text()
    author = Keyword()
    created_date = Date()
    
    # Multi-level join: site -> page -> comment -> reply
    content_join = Join(relations={
        'site': ['page', 'admin'],
        'page': 'comment',
        'comment': 'reply'
    })
    
    class Index:
        name = 'content'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

class JoinFieldService:
    """Advanced join field operations."""
    
    @staticmethod
    async def create_site(name: str, domain: str) -> str:
        """Create site (top-level parent)."""
        site = ContentDocument(
            title=name,
            content=f"Website: {domain}",
            author="system",
            created_date=datetime.utcnow(),
            content_join={'name': 'site'}
        )
        await site.save()
        return site.meta.id
    
    @staticmethod
    async def create_page(site_id: str, title: str, content: str, author: str) -> str:
        """Create page under site."""
        page = ContentDocument(
            title=title,
            content=content,
            author=author,
            created_date=datetime.utcnow(),
            content_join={
                'name': 'page',
                'parent': site_id
            }
        )
        await page.save(routing=site_id)
        return page.meta.id
    
    @staticmethod
    async def create_comment(
        page_id: str,
        content: str,
        author: str,
        site_id: str
    ) -> str:
        """Create comment under page."""
        comment = ContentDocument(
            title="Comment",
            content=content,
            author=author,
            created_date=datetime.utcnow(),
            content_join={
                'name': 'comment',
                'parent': page_id
            }
        )
        await comment.save(routing=site_id)
        return comment.meta.id
    
    @staticmethod
    async def create_reply(
        comment_id: str,
        content: str,
        author: str,
        site_id: str
    ) -> str:
        """Create reply under comment."""
        reply = ContentDocument(
            title="Reply",
            content=content,
            author=author,
            created_date=datetime.utcnow(),
            content_join={
                'name': 'reply',
                'parent': comment_id
            }
        )
        await reply.save(routing=site_id)
        return reply.meta.id
    
    @staticmethod
    async def get_site_hierarchy(site_id: str) -> Dict[str, Any]:
        """Get complete site hierarchy."""
        try:
            # Get site
            site = await ContentDocument.get(site_id)
            
            # Build hierarchy query
            search = AsyncSearch(index='content')
            search = search.filter('has_parent', parent_type='site', query=Q('term', _id=site_id))
            
            pages_response = await search.execute()
            
            site_data = {
                'id': site.meta.id,
                'title': site.title,
                'content': site.content,
                'pages': []
            }
            
            # Get pages and their comments
            for page_hit in pages_response.hits:
                page_data = {
                    'id': page_hit.meta.id,
                    'title': page_hit.title,
                    'content': page_hit.content,
                    'author': page_hit.author,
                    'comments': []
                }
                
                # Get comments for this page
                comments_search = AsyncSearch(index='content')
                comments_search = comments_search.filter(
                    'has_parent',
                    parent_type='page',
                    query=Q('term', _id=page_hit.meta.id)
                )
                
                comments_response = await comments_search.execute()
                
                for comment_hit in comments_response.hits:
                    comment_data = {
                        'id': comment_hit.meta.id,
                        'content': comment_hit.content,
                        'author': comment_hit.author,
                        'replies': []
                    }
                    
                    # Get replies for this comment
                    replies_search = AsyncSearch(index='content')
                    replies_search = replies_search.filter(
                        'has_parent',
                        parent_type='comment',
                        query=Q('term', _id=comment_hit.meta.id)
                    )
                    
                    replies_response = await replies_search.execute()
                    
                    for reply_hit in replies_response.hits:
                        comment_data['replies'].append({
                            'id': reply_hit.meta.id,
                            'content': reply_hit.content,
                            'author': reply_hit.author,
                            'created_date': reply_hit.created_date
                        })
                    
                    page_data['comments'].append(comment_data)
                
                site_data['pages'].append(page_data)
            
            return site_data
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get site hierarchy: {str(e)}"
            )
```

## Service Layer Management

### Unified Relationship Service
```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class RelationshipManager(ABC, Generic[T]):
    """Abstract base class for relationship management."""
    
    @abstractmethod
    async def create(self, data: T) -> str:
        """Create new document."""
        pass
    
    @abstractmethod
    async def get_with_relationships(self, doc_id: str) -> Dict[str, Any]:
        """Get document with resolved relationships."""
        pass
    
    @abstractmethod
    async def update_relationships(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update document relationships."""
        pass
    
    @abstractmethod
    async def delete_with_cascade(self, doc_id: str) -> bool:
        """Delete document and handle relationship cascade."""
        pass

class UnifiedRelationshipService:
    """Service that manages different relationship types."""
    
    def __init__(self):
        self.strategies = {
            'parent_child': ParentChildStrategy(),
            'reference': ReferenceStrategy(),
            'nested': NestedStrategy(),
            'denormalized': DenormalizedStrategy()
        }
    
    async def execute_operation(
        self,
        strategy_type: str,
        operation: str,
        **kwargs
    ) -> Any:
        """Execute operation using specified strategy."""
        if strategy_type not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_type}")
        
        strategy = self.strategies[strategy_type]
        
        if not hasattr(strategy, operation):
            raise ValueError(f"Strategy {strategy_type} doesn't support {operation}")
        
        return await getattr(strategy, operation)(**kwargs)
    
    async def migrate_relationship_type(
        self,
        from_strategy: str,
        to_strategy: str,
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """Migrate documents from one relationship type to another."""
        try:
            migration_results = {
                'migrated': [],
                'failed': [],
                'total': len(document_ids)
            }
            
            from_strategy_obj = self.strategies[from_strategy]
            to_strategy_obj = self.strategies[to_strategy]
            
            for doc_id in document_ids:
                try:
                    # Export data from source strategy
                    data = await from_strategy_obj.export_data(doc_id)
                    
                    # Import data to target strategy
                    new_id = await to_strategy_obj.import_data(data)
                    
                    migration_results['migrated'].append({
                        'old_id': doc_id,
                        'new_id': new_id
                    })
                    
                except Exception as e:
                    migration_results['failed'].append({
                        'id': doc_id,
                        'error': str(e)
                    })
            
            return migration_results
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {str(e)}"
            )

class RelationshipHealthChecker:
    """Check health and consistency of relationships."""
    
    @staticmethod
    async def check_reference_integrity(index_name: str) -> Dict[str, Any]:
        """Check if all references point to existing documents."""
        try:
            search = AsyncSearch(index=index_name)
            search = search.extra(size=1000)
            
            response = await search.execute()
            
            integrity_report = {
                'total_documents': response.hits.total.value,
                'broken_references': [],
                'orphaned_documents': [],
                'healthy_references': 0
            }
            
            for hit in response.hits:
                doc_data = hit.to_dict()
                
                # Check each reference field
                for field, value in doc_data.items():
                    if field.endswith('_id') or field.endswith('_ids'):
                        if isinstance(value, list):
                            # Multiple references
                            for ref_id in value:
                                if not await RelationshipHealthChecker._document_exists(ref_id):
                                    integrity_report['broken_references'].append({
                                        'document_id': hit.meta.id,
                                        'field': field,
                                        'broken_reference': ref_id
                                    })
                                else:
                                    integrity_report['healthy_references'] += 1
                        elif value:
                            # Single reference
                            if not await RelationshipHealthChecker._document_exists(value):
                                integrity_report['broken_references'].append({
                                    'document_id': hit.meta.id,
                                    'field': field,
                                    'broken_reference': value
                                })
                            else:
                                integrity_report['healthy_references'] += 1
            
            return integrity_report
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Integrity check failed: {str(e)}"
            )
    
    @staticmethod
    async def _document_exists(doc_id: str) -> bool:
        """Check if document exists in any index."""
        try:
            # This is a simplified check - in practice, you'd want to
            # know which index to check based on the reference type
            search = AsyncSearch()
            search = search.filter('term', _id=doc_id)
            search = search.extra(size=1)
            
            response = await search.execute()
            return response.hits.total.value > 0
            
        except Exception:
            return False
```

## Cross-Document Queries

### Advanced Query Patterns
```python
class CrossDocumentQueryService:
    """Service for complex cross-document queries."""
    
    @staticmethod
    async def search_articles_with_author_details(
        query: str,
        author_criteria: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search articles with author filtering."""
        try:
            # First, find matching authors if criteria provided
            author_ids = []
            if author_criteria:
                author_search = AsyncSearch(index='users')
                
                if 'bio_contains' in author_criteria:
                    author_search = author_search.query(
                        'match', bio=author_criteria['bio_contains']
                    )
                
                if 'created_after' in author_criteria:
                    author_search = author_search.filter(
                        'range', created_date={'gte': author_criteria['created_after']}
                    )
                
                author_response = await author_search.execute()
                author_ids = [hit.meta.id for hit in author_response.hits]
                
                if not author_ids:
                    return []  # No matching authors found
            
            # Search articles
            article_search = AsyncSearch(index='articles')
            article_search = article_search.query('multi_match', query=query, fields=['title', 'content'])
            
            # Filter by author IDs if provided
            if author_ids:
                article_search = article_search.filter('terms', author_id=author_ids)
            
            article_response = await article_search.execute()
            
            # Resolve author references
            unique_author_ids = list(set(
                hit.author_id for hit in article_response.hits
                if hasattr(hit, 'author_id')
            ))
            
            authors_map = {}
            if unique_author_ids:
                author_search = AsyncSearch(index='users')
                author_search = author_search.filter('terms', _id=unique_author_ids)
                author_search = author_search.extra(size=len(unique_author_ids))
                
                authors_response = await author_search.execute()
                authors_map = {
                    hit.meta.id: hit.to_dict() for hit in authors_response.hits
                }
            
            # Combine results
            results = []
            for hit in article_response.hits:
                article_data = hit.to_dict()
                article_data['id'] = hit.meta.id
                article_data['score'] = hit.meta.score
                
                # Add resolved author data
                if hit.author_id in authors_map:
                    article_data['author_details'] = authors_map[hit.author_id]
                
                results.append(article_data)
            
            return results
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cross-document search failed: {str(e)}"
            )
    
    @staticmethod
    async def get_related_content_by_categories(
        article_id: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Get related articles based on shared categories."""
        try:
            # Get source article
            try:
                article = await Article.get(article_id)
            except NotFoundError:
                raise HTTPException(status_code=404, detail="Article not found")
            
            if not article.category_ids:
                return []
            
            # Find related articles
            search = AsyncSearch(index='articles')
            search = search.query(
                'terms', category_ids=article.category_ids
            ).filter(
                'bool',
                must_not=[Q('term', _id=article_id)]  # Exclude source article
            )
            
            # Boost articles with more category matches
            search = search.extra(size=max_results * 2)  # Get more for scoring
            
            response = await search.execute()
            
            # Score by category overlap
            results = []
            for hit in response.hits:
                overlap_count = len(
                    set(article.category_ids) & set(hit.category_ids)
                )
                
                if overlap_count > 0:
                    article_data = hit.to_dict()
                    article_data['id'] = hit.meta.id
                    article_data['relevance_score'] = overlap_count
                    article_data['category_overlap'] = overlap_count
                    results.append(article_data)
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results[:max_results]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get related content: {str(e)}"
            )
    
    @staticmethod
    async def aggregate_data_across_relationships() -> Dict[str, Any]:
        """Perform complex aggregations across related documents."""
        try:
            # Multi-index aggregation query
            search = AsyncSearch(index=['articles', 'users', 'categories'])
            
            # Aggregate article counts by category
            search.aggs.bucket('categories', 'terms', field='category_ids', size=20)
            
            # Aggregate author activity
            search.aggs.bucket('authors', 'terms', field='author_id', size=10).metric(
                'avg_likes', 'avg', field='like_count'
            ).metric(
                'total_views', 'sum', field='view_count'
            )
            
            # Date histogram for article publishing trends
            search.aggs.bucket(
                'publishing_trends',
                'date_histogram',
                field='published_date',
                interval='month'
            ).metric('articles_per_month', 'value_count', field='published_date')
            
            response = await search.execute()
            
            aggregation_results = {
                'total_documents': response.hits.total.value,
                'categories': [],
                'top_authors': [],
                'publishing_trends': []
            }
            
            # Process category aggregation
            if hasattr(response.aggregations, 'categories'):
                for bucket in response.aggregations.categories.buckets:
                    aggregation_results['categories'].append({
                        'category_id': bucket.key,
                        'article_count': bucket.doc_count
                    })
            
            # Process author aggregation
            if hasattr(response.aggregations, 'authors'):
                for bucket in response.aggregations.authors.buckets:
                    aggregation_results['top_authors'].append({
                        'author_id': bucket.key,
                        'article_count': bucket.doc_count,
                        'avg_likes': bucket.avg_likes.value,
                        'total_views': bucket.total_views.value
                    })
            
            return aggregation_results
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cross-document aggregation failed: {str(e)}"
            )
```

## Performance Considerations

### Relationship Performance Optimization
```python
class RelationshipPerformanceOptimizer:
    """Tools for optimizing relationship performance."""
    
    @staticmethod
    async def analyze_relationship_performance(
        index_name: str,
        relationship_type: str
    ) -> Dict[str, Any]:
        """Analyze performance characteristics of relationships."""
        try:
            analysis = {
                'index_name': index_name,
                'relationship_type': relationship_type,
                'recommendations': [],
                'metrics': {}
            }
            
            # Get index statistics
            search = AsyncSearch(index=index_name)
            search.aggs.bucket('doc_count', 'value_count', field='_id')
            
            if relationship_type == 'parent_child':
                # Analyze parent-child distribution
                search.aggs.bucket('parent_types', 'terms', field='join_field.name')
                
            elif relationship_type == 'reference':
                # Analyze reference patterns
                search.aggs.bucket('reference_fields', 'terms', field='*_id')
                
            elif relationship_type == 'nested':
                # Analyze nested document sizes
                search.aggs.metric('avg_nested_size', 'avg', script={
                    'source': 'params._source.nested_field.size()',
                    'lang': 'painless'
                })
            
            response = await search.execute()
            
            # Add performance recommendations based on analysis
            if relationship_type == 'parent_child':
                analysis['recommendations'].extend([
                    "Consider denormalizing if parent-child ratio is high",
                    "Use routing for better query performance",
                    "Monitor shard distribution for parent documents"
                ])
            
            elif relationship_type == 'reference':
                analysis['recommendations'].extend([
                    "Implement reference caching for frequently accessed data",
                    "Consider denormalizing read-heavy referenced fields",
                    "Use bulk resolution for multiple references"
                ])
            
            elif relationship_type == 'nested':
                analysis['recommendations'].extend([
                    "Limit nested document array sizes for better performance",
                    "Use include_in_parent for frequently queried nested fields",
                    "Consider flattening if nested queries are rare"
                ])
            
            return analysis
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Performance analysis failed: {str(e)}"
            )
    
    @staticmethod
    async def optimize_relationship_queries(
        original_query: Dict[str, Any],
        relationship_type: str
    ) -> Dict[str, Any]:
        """Optimize queries based on relationship type."""
        try:
            optimized_query = original_query.copy()
            
            if relationship_type == 'parent_child':
                # Add routing for parent-child queries
                if 'has_parent' in str(original_query) or 'has_child' in str(original_query):
                    optimized_query['routing'] = 'parent_id'
            
            elif relationship_type == 'nested':
                # Optimize nested queries
                if 'nested' in str(original_query):
                    # Add inner_hits for better performance
                    optimized_query.setdefault('inner_hits', {
                        'size': 3,  # Limit inner hits
                        '_source': False  # Don't return full nested docs
                    })
            
            elif relationship_type == 'reference':
                # Suggest using denormalized fields instead of joins
                optimized_query['_source'] = {
                    'includes': ['*'],
                    'excludes': ['*_full_reference']  # Exclude heavy reference data
                }
            
            return optimized_query
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Query optimization failed: {str(e)}"
            )

# Performance monitoring
class RelationshipMetrics:
    """Metrics collection for relationship performance."""
    
    def __init__(self):
        self.query_times = {}
        self.error_counts = {}
        self.cache_hit_rates = {}
    
    async def record_query_time(
        self,
        relationship_type: str,
        operation: str,
        execution_time: float
    ):
        """Record query execution time."""
        key = f"{relationship_type}_{operation}"
        if key not in self.query_times:
            self.query_times[key] = []
        
        self.query_times[key].append(execution_time)
        
        # Keep only last 100 measurements
        if len(self.query_times[key]) > 100:
            self.query_times[key] = self.query_times[key][-100:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all relationship types."""
        summary = {}
        
        for key, times in self.query_times.items():
            if times:
                summary[key] = {
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times),
                    'min_time': min(times),
                    'query_count': len(times)
                }
        
        return summary
```

## Next Steps

1. **[Schema Design](03_schema-design.md)** - Learn efficient index design patterns
2. **[Serialization Patterns](04_serialization-patterns.md)** - Master data transformation techniques
3. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Advanced optimization strategies

## Additional Resources

- **Elasticsearch Join Documentation**: [elastic.co/guide/en/elasticsearch/reference/current/parent-join.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/parent-join.html)
- **Nested Objects Guide**: [elastic.co/guide/en/elasticsearch/reference/current/nested.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html)
- **FastAPI Background Tasks**: [fastapi.tiangolo.com/tutorial/background-tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)