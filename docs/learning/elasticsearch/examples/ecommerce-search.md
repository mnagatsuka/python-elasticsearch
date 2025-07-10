# E-commerce Search Implementation

**Build a comprehensive product search system with faceting, recommendations, and analytics**

*Implementation time: 2-3 hours*

## Overview

This example demonstrates building a complete e-commerce search solution using Elasticsearch. We'll implement product search, filtering, recommendations, and analytics commonly found in modern e-commerce platforms.

## 🎯 Features Implemented

- **Product Search** - Full-text search across product names, descriptions, and categories
- **Faceted Navigation** - Filters by category, brand, price range, ratings
- **Auto-suggestions** - Search-as-you-type functionality
- **Recommendations** - "Similar products" and "Customers also viewed"
- **Analytics** - Search analytics, popular products, conversion tracking
- **Inventory Integration** - Real-time stock levels and availability

## 🏗️ Architecture Overview

```
Frontend (React/Vue) 
     ↓
API Gateway (FastAPI/Express)
     ↓
Elasticsearch Cluster
     ↓
Data Pipeline (Logstash/Python)
     ↓
Product Database (MySQL/PostgreSQL)
```

## 📋 Prerequisites

- Elasticsearch 8.x cluster
- Python 3.8+ with elasticsearch library
- Sample product dataset
- Basic understanding of REST APIs

## 🚀 Quick Start

### 1. Setup Elasticsearch Index

**Create Product Index:**
```bash
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "product_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "stop",
            "synonyms"
          ]
        },
        "autocomplete_analyzer": {
          "type": "custom",
          "tokenizer": "keyword",
          "filter": [
            "lowercase",
            "edge_ngram"
          ]
        }
      },
      "filter": {
        "synonyms": {
          "type": "synonym",
          "synonyms": [
            "laptop,notebook,computer",
            "mobile,phone,smartphone",
            "tv,television"
          ]
        },
        "edge_ngram": {
          "type": "edge_ngram",
          "min_gram": 1,
          "max_gram": 20
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "name": {
        "type": "text",
        "analyzer": "product_analyzer",
        "fields": {
          "suggest": {
            "type": "text",
            "analyzer": "autocomplete_analyzer"
          },
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "description": {
        "type": "text",
        "analyzer": "product_analyzer"
      },
      "category": {
        "type": "keyword"
      },
      "brand": {
        "type": "keyword"
      },
      "price": {
        "type": "float"
      },
      "sale_price": {
        "type": "float"
      },
      "rating": {
        "type": "float"
      },
      "review_count": {
        "type": "integer"
      },
      "stock_quantity": {
        "type": "integer"
      },
      "tags": {
        "type": "keyword"
      },
      "attributes": {
        "type": "nested",
        "properties": {
          "name": {"type": "keyword"},
          "value": {"type": "keyword"}
        }
      },
      "images": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date"
      },
      "updated_at": {
        "type": "date"
      },
      "is_active": {
        "type": "boolean"
      },
      "sales_count": {
        "type": "integer"
      },
      "view_count": {
        "type": "integer"
      }
    }
  }
}
'
```

### 2. Sample Data Generation

**Python Script to Generate Sample Products:**
```python
#!/usr/bin/env python3

import json
import random
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

# Sample data
CATEGORIES = [
    "Electronics", "Clothing", "Books", "Home & Garden", 
    "Sports & Outdoors", "Health & Beauty", "Toys & Games"
]

BRANDS = [
    "TechCorp", "StyleMax", "BookWorld", "HomeSpace", 
    "SportsPro", "BeautyPlus", "ToyLand", "GenericBrand"
]

ELECTRONICS = [
    "Smartphone", "Laptop", "Tablet", "Headphones", "Camera", 
    "Speaker", "Monitor", "Keyboard", "Mouse", "TV"
]

CLOTHING = [
    "T-Shirt", "Jeans", "Dress", "Jacket", "Sneakers", 
    "Hoodie", "Sweater", "Shorts", "Skirt", "Boots"
]

def generate_product(product_id):
    category = random.choice(CATEGORIES)
    brand = random.choice(BRANDS)
    
    if category == "Electronics":
        base_name = random.choice(ELECTRONICS)
    elif category == "Clothing":
        base_name = random.choice(CLOTHING)
    else:
        base_name = f"{category} Item"
    
    name = f"{brand} {base_name}"
    
    base_price = random.uniform(10, 1000)
    is_on_sale = random.choice([True, False])
    sale_price = base_price * 0.8 if is_on_sale else None
    
    return {
        "id": f"PROD_{product_id:06d}",
        "name": name,
        "description": f"High quality {base_name.lower()} from {brand}. Perfect for daily use with excellent features and durability.",
        "category": category,
        "brand": brand,
        "price": round(base_price, 2),
        "sale_price": round(sale_price, 2) if sale_price else None,
        "rating": round(random.uniform(3.0, 5.0), 1),
        "review_count": random.randint(0, 500),
        "stock_quantity": random.randint(0, 100),
        "tags": random.sample(["popular", "new", "sale", "featured", "trending"], k=random.randint(1, 3)),
        "attributes": [
            {"name": "color", "value": random.choice(["Red", "Blue", "Green", "Black", "White"])},
            {"name": "size", "value": random.choice(["S", "M", "L", "XL"])}
        ],
        "images": [f"https://example.com/images/{product_id}_1.jpg"],
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": random.choice([True, True, True, False]),  # 75% active
        "sales_count": random.randint(0, 1000),
        "view_count": random.randint(0, 5000)
    }

def index_products(es, num_products=1000):
    print(f"Generating and indexing {num_products} products...")
    
    for i in range(1, num_products + 1):
        product = generate_product(i)
        
        try:
            es.index(
                index="products",
                id=product["id"],
                body=product
            )
            
            if i % 100 == 0:
                print(f"Indexed {i} products...")
                
        except Exception as e:
            print(f"Error indexing product {i}: {e}")
    
    print(f"Successfully indexed {num_products} products!")

if __name__ == "__main__":
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    index_products(es, 1000)
```

### 3. Search API Implementation

**FastAPI Backend:**
```python
#!/usr/bin/env python3

from fastapi import FastAPI, Query, HTTPException
from elasticsearch import Elasticsearch
from typing import Optional, List, Dict, Any
import json

app = FastAPI(title="E-commerce Search API")
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

class SearchResponse:
    def __init__(self, hits, total, aggregations=None, suggestions=None):
        self.products = []
        self.total = total
        self.aggregations = aggregations or {}
        self.suggestions = suggestions or []
        
        for hit in hits:
            product = hit['_source']
            product['score'] = hit['_score']
            self.products.append(product)

@app.get("/search")
async def search_products(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    in_stock: Optional[bool] = Query(None, description="Only show in-stock items"),
    sort_by: Optional[str] = Query("relevance", description="Sort by: relevance, price_asc, price_desc, rating, newest"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Number of results per page")
):
    """Search products with filters and faceting"""
    
    # Build query
    query = {
        "bool": {
            "must": [],
            "filter": []
        }
    }
    
    # Text search
    if q:
        query["bool"]["must"].append({
            "multi_match": {
                "query": q,
                "fields": [
                    "name^3",
                    "description",
                    "brand^2",
                    "category^2",
                    "tags^1.5"
                ],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })
    else:
        query["bool"]["must"].append({"match_all": {}})
    
    # Filters
    if category:
        query["bool"]["filter"].append({"term": {"category": category}})
    
    if brand:
        query["bool"]["filter"].append({"term": {"brand": brand}})
    
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price
        query["bool"]["filter"].append({"range": {"price": price_range}})
    
    if min_rating is not None:
        query["bool"]["filter"].append({"range": {"rating": {"gte": min_rating}}})
    
    if in_stock:
        query["bool"]["filter"].append({"range": {"stock_quantity": {"gt": 0}}})
    
    # Only active products
    query["bool"]["filter"].append({"term": {"is_active": True}})
    
    # Sorting
    sort_options = {
        "relevance": [],  # Default ES scoring
        "price_asc": [{"price": {"order": "asc"}}],
        "price_desc": [{"price": {"order": "desc"}}],
        "rating": [{"rating": {"order": "desc"}}, {"review_count": {"order": "desc"}}],
        "newest": [{"created_at": {"order": "desc"}}],
        "popular": [{"sales_count": {"order": "desc"}}, {"view_count": {"order": "desc"}}]
    }
    
    sort = sort_options.get(sort_by, [])
    
    # Aggregations for faceting
    aggs = {
        "categories": {
            "terms": {"field": "category", "size": 20}
        },
        "brands": {
            "terms": {"field": "brand", "size": 20}
        },
        "price_ranges": {
            "range": {
                "field": "price",
                "ranges": [
                    {"key": "Under $25", "to": 25},
                    {"key": "$25 - $50", "from": 25, "to": 50},
                    {"key": "$50 - $100", "from": 50, "to": 100},
                    {"key": "$100 - $250", "from": 100, "to": 250},
                    {"key": "$250+", "from": 250}
                ]
            }
        },
        "ratings": {
            "range": {
                "field": "rating",
                "ranges": [
                    {"key": "4+ Stars", "from": 4},
                    {"key": "3+ Stars", "from": 3},
                    {"key": "2+ Stars", "from": 2},
                    {"key": "1+ Stars", "from": 1}
                ]
            }
        },
        "availability": {
            "terms": {
                "script": {
                    "source": "doc['stock_quantity'].value > 0 ? 'In Stock' : 'Out of Stock'"
                }
            }
        }
    }
    
    # Search request
    search_body = {
        "query": query,
        "sort": sort,
        "from": (page - 1) * size,
        "size": size,
        "aggs": aggs,
        "_source": {
            "excludes": ["description"]  # Exclude large fields for list view
        }
    }
    
    try:
        response = es.search(index="products", body=search_body)
        
        search_result = SearchResponse(
            hits=response['hits']['hits'],
            total=response['hits']['total']['value'],
            aggregations=response.get('aggregations', {})
        )
        
        return {
            "products": search_result.products,
            "total": search_result.total,
            "page": page,
            "size": size,
            "facets": {
                "categories": [
                    {"name": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in search_result.aggregations.get("categories", {}).get("buckets", [])
                ],
                "brands": [
                    {"name": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in search_result.aggregations.get("brands", {}).get("buckets", [])
                ],
                "price_ranges": [
                    {"name": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in search_result.aggregations.get("price_ranges", {}).get("buckets", [])
                ],
                "ratings": [
                    {"name": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in search_result.aggregations.get("ratings", {}).get("buckets", [])
                ],
                "availability": [
                    {"name": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in search_result.aggregations.get("availability", {}).get("buckets", [])
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/suggest")
async def autocomplete(
    q: str = Query(..., min_length=1, description="Search query for suggestions"),
    size: int = Query(5, ge=1, le=20, description="Number of suggestions")
):
    """Get search suggestions for autocomplete"""
    
    suggest_body = {
        "suggest": {
            "product_suggest": {
                "prefix": q,
                "completion": {
                    "field": "name.suggest",
                    "size": size
                }
            }
        }
    }
    
    # Also search for matching product names
    search_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "name.suggest": {
                                "query": q,
                                "operator": "and"
                            }
                        }
                    }
                ],
                "filter": [
                    {"term": {"is_active": True}}
                ]
            }
        },
        "size": size,
        "_source": ["name", "category", "brand"]
    }
    
    try:
        search_response = es.search(index="products", body=search_body)
        
        suggestions = []
        for hit in search_response['hits']['hits']:
            suggestions.append({
                "text": hit['_source']['name'],
                "category": hit['_source']['category'],
                "brand": hit['_source']['brand']
            })
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion error: {str(e)}")

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get detailed product information"""
    
    try:
        response = es.get(index="products", id=product_id)
        return response['_source']
        
    except Exception as e:
        raise HTTPException(status_code=404, detail="Product not found")

@app.get("/products/{product_id}/similar")
async def get_similar_products(
    product_id: str,
    size: int = Query(10, ge=1, le=20, description="Number of similar products")
):
    """Get products similar to the given product"""
    
    try:
        # Get the original product
        product_response = es.get(index="products", id=product_id)
        product = product_response['_source']
        
        # Find similar products using More Like This
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "more_like_this": {
                                "fields": ["name", "description", "category", "brand"],
                                "like": [
                                    {
                                        "_index": "products",
                                        "_id": product_id
                                    }
                                ],
                                "min_term_freq": 1,
                                "min_doc_freq": 1,
                                "max_query_terms": 20
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"is_active": True}},
                        {"range": {"stock_quantity": {"gt": 0}}}
                    ],
                    "must_not": [
                        {"term": {"id": product_id}}
                    ]
                }
            },
            "size": size,
            "_source": {
                "excludes": ["description"]
            }
        }
        
        response = es.search(index="products", body=search_body)
        
        similar_products = []
        for hit in response['hits']['hits']:
            product = hit['_source']
            product['similarity_score'] = hit['_score']
            similar_products.append(product)
        
        return {"similar_products": similar_products}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar products error: {str(e)}")

@app.get("/analytics/popular")
async def get_popular_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    time_period: str = Query("week", description="Time period: day, week, month"),
    size: int = Query(10, ge=1, le=50, description="Number of products")
):
    """Get popular products based on views and sales"""
    
    # Calculate date range
    from datetime import datetime, timedelta
    
    time_deltas = {
        "day": timedelta(days=1),
        "week": timedelta(weeks=1),
        "month": timedelta(days=30)
    }
    
    since_date = datetime.now() - time_deltas.get(time_period, timedelta(weeks=1))
    
    query = {
        "bool": {
            "filter": [
                {"term": {"is_active": True}},
                {"range": {"updated_at": {"gte": since_date.isoformat()}}}
            ]
        }
    }
    
    if category:
        query["bool"]["filter"].append({"term": {"category": category}})
    
    search_body = {
        "query": query,
        "sort": [
            {"sales_count": {"order": "desc"}},
            {"view_count": {"order": "desc"}},
            {"rating": {"order": "desc"}}
        ],
        "size": size,
        "_source": {
            "excludes": ["description"]
        }
    }
    
    try:
        response = es.search(index="products", body=search_body)
        
        popular_products = []
        for hit in response['hits']['hits']:
            popular_products.append(hit['_source'])
        
        return {"popular_products": popular_products}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Popular products error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4. Frontend Implementation

**React Search Component:**
```jsx
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { debounce } from 'lodash';

const API_BASE = 'http://localhost:8000';

const ProductSearch = () => {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [facets, setFacets] = useState({});
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filters, setFilters] = useState({
    category: '',
    brand: '',
    min_price: '',
    max_price: '',
    min_rating: '',
    in_stock: false
  });
  const [sortBy, setSortBy] = useState('relevance');
  const [page, setPage] = useState(1);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (searchQuery, searchFilters, searchSort, searchPage) => {
      setLoading(true);
      try {
        const params = {
          q: searchQuery,
          sort_by: searchSort,
          page: searchPage,
          ...searchFilters
        };
        
        // Remove empty filters
        Object.keys(params).forEach(key => {
          if (params[key] === '' || params[key] === null) {
            delete params[key];
          }
        });

        const response = await axios.get(`${API_BASE}/search`, { params });
        setProducts(response.data.products);
        setFacets(response.data.facets);
        setTotal(response.data.total);
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  // Debounced suggestions
  const debouncedSuggestions = useCallback(
    debounce(async (searchQuery) => {
      if (searchQuery.length > 1) {
        try {
          const response = await axios.get(`${API_BASE}/suggest`, {
            params: { q: searchQuery }
          });
          setSuggestions(response.data.suggestions);
          setShowSuggestions(true);
        } catch (error) {
          console.error('Suggestions error:', error);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 200),
    []
  );

  // Search effect
  useEffect(() => {
    debouncedSearch(query, filters, sortBy, page);
  }, [query, filters, sortBy, page, debouncedSearch]);

  // Suggestions effect
  useEffect(() => {
    debouncedSuggestions(query);
  }, [query, debouncedSuggestions]);

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
    setPage(1);
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
    setPage(1);
  };

  const handleSortChange = (e) => {
    setSortBy(e.target.value);
    setPage(1);
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion.text);
    setShowSuggestions(false);
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  return (
    <div className="product-search">
      {/* Search Header */}
      <div className="search-header">
        <div className="search-box-container">
          <input
            type="text"
            value={query}
            onChange={handleQueryChange}
            placeholder="Search products..."
            className="search-input"
          />
          
          {showSuggestions && suggestions.length > 0 && (
            <div className="suggestions-dropdown">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="suggestion-item"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  <strong>{suggestion.text}</strong>
                  <span className="suggestion-meta">
                    {suggestion.brand} - {suggestion.category}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="sort-controls">
          <select value={sortBy} onChange={handleSortChange}>
            <option value="relevance">Relevance</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="rating">Customer Rating</option>
            <option value="newest">Newest</option>
            <option value="popular">Most Popular</option>
          </select>
        </div>
      </div>

      <div className="search-content">
        {/* Filters Sidebar */}
        <div className="filters-sidebar">
          <h3>Filters</h3>
          
          {/* Category Filter */}
          {facets.categories && facets.categories.length > 0 && (
            <div className="filter-group">
              <h4>Category</h4>
              {facets.categories.map(category => (
                <label key={category.name} className="filter-item">
                  <input
                    type="radio"
                    name="category"
                    value={category.name}
                    checked={filters.category === category.name}
                    onChange={(e) => handleFilterChange('category', e.target.value)}
                  />
                  {category.name} ({category.count})
                </label>
              ))}
              {filters.category && (
                <button onClick={() => handleFilterChange('category', '')}>
                  Clear
                </button>
              )}
            </div>
          )}

          {/* Brand Filter */}
          {facets.brands && facets.brands.length > 0 && (
            <div className="filter-group">
              <h4>Brand</h4>
              {facets.brands.slice(0, 10).map(brand => (
                <label key={brand.name} className="filter-item">
                  <input
                    type="radio"
                    name="brand"
                    value={brand.name}
                    checked={filters.brand === brand.name}
                    onChange={(e) => handleFilterChange('brand', e.target.value)}
                  />
                  {brand.name} ({brand.count})
                </label>
              ))}
              {filters.brand && (
                <button onClick={() => handleFilterChange('brand', '')}>
                  Clear
                </button>
              )}
            </div>
          )}

          {/* Price Range Filter */}
          <div className="filter-group">
            <h4>Price Range</h4>
            <div className="price-inputs">
              <input
                type="number"
                placeholder="Min"
                value={filters.min_price}
                onChange={(e) => handleFilterChange('min_price', e.target.value)}
              />
              <input
                type="number"
                placeholder="Max"
                value={filters.max_price}
                onChange={(e) => handleFilterChange('max_price', e.target.value)}
              />
            </div>
          </div>

          {/* Rating Filter */}
          <div className="filter-group">
            <h4>Minimum Rating</h4>
            <select
              value={filters.min_rating}
              onChange={(e) => handleFilterChange('min_rating', e.target.value)}
            >
              <option value="">Any Rating</option>
              <option value="4">4+ Stars</option>
              <option value="3">3+ Stars</option>
              <option value="2">2+ Stars</option>
            </select>
          </div>

          {/* Stock Filter */}
          <div className="filter-group">
            <label className="filter-item">
              <input
                type="checkbox"
                checked={filters.in_stock}
                onChange={(e) => handleFilterChange('in_stock', e.target.checked)}
              />
              In Stock Only
            </label>
          </div>
        </div>

        {/* Results */}
        <div className="results-content">
          <div className="results-header">
            <h2>
              {total.toLocaleString()} Products Found
              {query && ` for "${query}"`}
            </h2>
          </div>

          {loading ? (
            <div className="loading">Searching...</div>
          ) : (
            <>
              <div className="products-grid">
                {products.map(product => (
                  <div key={product.id} className="product-card">
                    <div className="product-image">
                      <img 
                        src={product.images?.[0] || '/placeholder.jpg'} 
                        alt={product.name}
                      />
                      {product.stock_quantity === 0 && (
                        <div className="out-of-stock-overlay">Out of Stock</div>
                      )}
                    </div>
                    
                    <div className="product-info">
                      <h3 className="product-name">{product.name}</h3>
                      <p className="product-brand">{product.brand}</p>
                      
                      <div className="product-rating">
                        <span className="rating-stars">
                          {'★'.repeat(Math.floor(product.rating))}
                          {'☆'.repeat(5 - Math.floor(product.rating))}
                        </span>
                        <span className="rating-text">
                          {product.rating} ({product.review_count} reviews)
                        </span>
                      </div>
                      
                      <div className="product-price">
                        {product.sale_price ? (
                          <>
                            <span className="sale-price">{formatPrice(product.sale_price)}</span>
                            <span className="original-price">{formatPrice(product.price)}</span>
                          </>
                        ) : (
                          <span className="price">{formatPrice(product.price)}</span>
                        )}
                      </div>

                      {product.tags && product.tags.length > 0 && (
                        <div className="product-tags">
                          {product.tags.map(tag => (
                            <span key={tag} className="tag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {total > 20 && (
                <div className="pagination">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </button>
                  
                  <span>Page {page} of {Math.ceil(total / 20)}</span>
                  
                  <button
                    disabled={page >= Math.ceil(total / 20)}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductSearch;
```

### 5. Analytics Dashboard

**Search Analytics API:**
```python
@app.get("/analytics/search")
async def search_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get search analytics data"""
    
    # This would typically come from a separate analytics index
    # For demo purposes, we'll simulate some analytics data
    
    from datetime import datetime, timedelta
    import random
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Simulate analytics data
    analytics_data = {
        "total_searches": random.randint(1000, 5000),
        "unique_users": random.randint(500, 2000),
        "avg_results_per_search": round(random.uniform(10, 50), 1),
        "zero_result_searches": random.randint(50, 200),
        "top_search_terms": [
            {"term": "laptop", "count": random.randint(100, 500)},
            {"term": "smartphone", "count": random.randint(80, 400)},
            {"term": "headphones", "count": random.randint(60, 300)},
            {"term": "tablet", "count": random.randint(40, 200)},
            {"term": "camera", "count": random.randint(30, 150)}
        ],
        "search_volume_by_day": [
            {
                "date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                "searches": random.randint(100, 800)
            }
            for i in range(7, 0, -1)
        ],
        "conversion_rate": round(random.uniform(2, 8), 2),
        "avg_session_duration": f"{random.randint(3, 12)}m {random.randint(10, 59)}s"
    }
    
    return analytics_data

@app.post("/analytics/track")
async def track_event(
    event_type: str,
    product_id: Optional[str] = None,
    search_query: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Track user events for analytics"""
    
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,  # view, click, purchase, search
        "product_id": product_id,
        "search_query": search_query,
        "user_id": user_id,
        "session_id": session_id
    }
    
    # In a real implementation, you would:
    # 1. Store this in an analytics index
    # 2. Update product view counts
    # 3. Update search analytics
    
    try:
        # Example: Update product view count
        if event_type == "view" and product_id:
            es.update(
                index="products",
                id=product_id,
                body={
                    "script": {
                        "source": "ctx._source.view_count += 1"
                    }
                }
            )
        
        return {"status": "tracked"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tracking error: {str(e)}")
```

## 🔧 Advanced Features

### Performance Optimization

**Index Optimization:**
```bash
# Force merge for better search performance
curl -X POST "localhost:9200/products/_forcemerge?max_num_segments=1"

# Update index settings for production
curl -X PUT "localhost:9200/products/_settings" -H 'Content-Type: application/json' -d'
{
  "refresh_interval": "30s",
  "number_of_replicas": 1
}
'
```

### Personalization

**User-based Recommendations:**
```python
@app.get("/recommendations/{user_id}")
async def get_user_recommendations(
    user_id: str,
    size: int = Query(10, description="Number of recommendations")
):
    """Get personalized recommendations for a user"""
    
    # This would typically use:
    # 1. User's purchase history
    # 2. Browsing behavior
    # 3. Collaborative filtering
    # 4. Machine learning models
    
    # For demo, we'll use a simplified approach
    search_body = {
        "query": {
            "function_score": {
                "query": {"match_all": {}},
                "functions": [
                    {
                        "filter": {"term": {"category": "Electronics"}},
                        "weight": 1.5
                    },
                    {
                        "field_value_factor": {
                            "field": "rating",
                            "factor": 0.1,
                            "modifier": "log1p"
                        }
                    },
                    {
                        "random_score": {
                            "seed": hash(user_id) % 1000,
                            "field": "_seq_no"
                        }
                    }
                ],
                "score_mode": "multiply",
                "boost_mode": "multiply"
            }
        },
        "filter": [
            {"term": {"is_active": True}},
            {"range": {"stock_quantity": {"gt": 0}}}
        ],
        "size": size
    }
    
    try:
        response = es.search(index="products", body=search_body)
        recommendations = [hit['_source'] for hit in response['hits']['hits']]
        return {"recommendations": recommendations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations error: {str(e)}")
```

## 📊 Monitoring and Analytics

### Search Performance Monitoring

```python
import time
from functools import wraps

def monitor_search_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # Log successful search
            duration = time.time() - start_time
            print(f"Search completed in {duration:.2f}s")
            
            # Track in analytics (would typically go to a separate index)
            # analytics_data = {
            #     "timestamp": datetime.now().isoformat(),
            #     "endpoint": func.__name__,
            #     "duration_ms": duration * 1000,
            #     "status": "success",
            #     "result_count": len(result.get("products", []))
            # }
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"Search failed after {duration:.2f}s: {e}")
            raise
            
    return wrapper

# Apply to search endpoints
search_products = monitor_search_performance(search_products)
```

## 🚀 Deployment

### Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - elasticsearch
    environment:
      - ES_HOST=elasticsearch:9200

volumes:
  es_data:
```

## 📚 Next Steps

1. **Implement A/B Testing** - Test different search algorithms and UI designs
2. **Add Machine Learning** - Implement learning-to-rank and personalization
3. **Scale for Production** - Add caching, load balancing, and monitoring
4. **Enhance Security** - Add authentication, rate limiting, and input validation
5. **Mobile Optimization** - Create responsive design and mobile-specific features

## 🔗 Related Examples

- **[Autocomplete & Suggestions](autocomplete-suggestions.md)** - Advanced search-as-you-type
- **[Real-time Analytics](realtime-analytics.md)** - Live search analytics dashboard
- **[Performance Monitoring](performance-monitoring.md)** - Monitor search performance

This e-commerce search implementation provides a solid foundation for building scalable, feature-rich product search experiences with Elasticsearch!