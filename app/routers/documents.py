from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.document_service import DocumentService

router = APIRouter()


class ArticleCreate(BaseModel):
    title: str
    content: str
    author: str
    category: str
    tags: List[str] = []
    views: int = 0
    rating: float = 0.0


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    views: Optional[int] = None
    rating: Optional[float] = None


class ArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    author: str
    category: str
    tags: List[str]
    views: int
    rating: float
    created_at: str
    updated_at: str


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    bio: str = ""
    is_active: str = "true"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    bio: str
    is_active: str
    created_at: str
    updated_at: str


@router.post("/articles", response_model=ArticleResponse)
async def create_article(article: ArticleCreate):
    """Create a new article"""
    try:
        created_article = await DocumentService.create_article(article.dict())
        return ArticleResponse(
            id=created_article.meta.id,
            title=created_article.title,
            content=created_article.content,
            author=created_article.author,
            category=created_article.category,
            tags=created_article.tags,
            views=created_article.views,
            rating=created_article.rating,
            created_at=created_article.created_at.isoformat(),
            updated_at=created_article.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str):
    """Get an article by ID"""
    article = await DocumentService.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleResponse(
        id=article.meta.id,
        title=article.title,
        content=article.content,
        author=article.author,
        category=article.category,
        tags=article.tags,
        views=article.views,
        rating=article.rating,
        created_at=article.created_at.isoformat(),
        updated_at=article.updated_at.isoformat()
    )


@router.get("/articles", response_model=List[ArticleResponse])
async def search_articles(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Search articles with filters"""
    try:
        articles = await DocumentService.search_articles(
            query=query,
            category=category,
            tags=tags,
            limit=limit,
            offset=offset
        )
        
        return [
            ArticleResponse(
                id=article.meta.id,
                title=article.title,
                content=article.content,
                author=article.author,
                category=article.category,
                tags=article.tags,
                views=article.views,
                rating=article.rating,
                created_at=article.created_at.isoformat(),
                updated_at=article.updated_at.isoformat()
            )
            for article in articles
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, article_update: ArticleUpdate):
    """Update an article"""
    try:
        update_data = {k: v for k, v in article_update.dict().items() if v is not None}
        updated_article = await DocumentService.update_article(article_id, update_data)
        
        if not updated_article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return ArticleResponse(
            id=updated_article.meta.id,
            title=updated_article.title,
            content=updated_article.content,
            author=updated_article.author,
            category=updated_article.category,
            tags=updated_article.tags,
            views=updated_article.views,
            rating=updated_article.rating,
            created_at=updated_article.created_at.isoformat(),
            updated_at=updated_article.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/articles/{article_id}")
async def delete_article(article_id: str):
    """Delete an article"""
    try:
        deleted = await DocumentService.delete_article(article_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return {"message": "Article deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        created_user = await DocumentService.create_user(user.dict())
        return UserResponse(
            id=created_user.meta.id,
            username=created_user.username,
            email=created_user.email,
            full_name=created_user.full_name,
            bio=created_user.bio,
            is_active=created_user.is_active,
            created_at=created_user.created_at.isoformat(),
            updated_at=created_user.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get a user by ID"""
    user = await DocumentService.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.meta.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        bio=user.bio,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )