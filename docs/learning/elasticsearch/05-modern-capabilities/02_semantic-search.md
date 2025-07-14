# Semantic Search

**Implement natural language understanding with semantic text fields and AI-powered search**

*Estimated reading time: 35 minutes*

## Overview

Semantic search goes beyond keyword matching to understand the meaning and intent behind queries. With Elasticsearch 9.0's semantic_text field type and integrated inference capabilities, you can build search experiences that understand natural language, context, and user intent.

## 📋 Table of Contents

1. [Semantic Search Fundamentals](#semantic-search-fundamentals)
2. [Semantic Text Field](#semantic-text-field)
3. [Inference Integration](#inference-integration)
4. [Natural Language Queries](#natural-language-queries)
5. [Contextual Search](#contextual-search)
6. [Performance & Scaling](#performance--scaling)
7. [Advanced Applications](#advanced-applications)

## 🧠 Semantic Search Fundamentals

### What is Semantic Search?

Semantic search understands the meaning behind words and phrases, not just exact matches. It considers context, synonyms, intent, and relationships between concepts.

**Traditional Keyword Search:**
```
Query: "apple fruit nutrition"
Matches: Documents containing "apple", "fruit", "nutrition"
Misses: "vitamin content of apples", "nutritional benefits of eating apples"
```

**Semantic Search:**
```
Query: "apple fruit nutrition"
Understands: User wants nutritional information about apples (the fruit)
Matches: "vitamin content", "health benefits", "dietary value", "minerals in apples"
Excludes: Apple Inc. technology content
```

### Key Capabilities

- **Intent Understanding**: Recognizes what users are really looking for
- **Contextual Awareness**: Understands words in context
- **Synonym Recognition**: Finds semantically similar terms
- **Concept Relationships**: Understands hierarchical and associative relationships
- **Multilingual Support**: Works across languages with shared semantic space

## 📝 Semantic Text Field

### Basic Semantic Text Field

The `semantic_text` field type (GA in Elasticsearch 9.0) automatically handles embedding generation and vector search:

```bash
curl -X PUT "localhost:9200/articles" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "content": {"type": "text"},
      "semantic_content": {
        "type": "semantic_text",
        "inference_id": "my_embedding_model"
      },
      "semantic_title": {
        "type": "semantic_text", 
        "inference_id": "my_embedding_model"
      }
    }
  }
}
'
```

### Field Configuration

```bash
curl -X PUT "localhost:9200/knowledge_base" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "content": {"type": "text"},
      "category": {"type": "keyword"},
      "semantic_content": {
        "type": "semantic_text",
        "inference_id": "sentence_transformer_model",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 384,
          "similarity": "cosine"
        }
      }
    }
  }
}
'
```

### Indexing with Semantic Fields

```bash
# Index documents - embeddings generated automatically
curl -X POST "localhost:9200/articles/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Understanding Machine Learning",
  "content": "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
  "semantic_content": "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
  "category": "AI"
}
'

# Bulk indexing
curl -X POST "localhost:9200/articles/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_id": "2"}}
{"title": "Deep Learning Neural Networks", "semantic_content": "Deep learning uses multi-layer neural networks to model complex patterns in data", "category": "AI"}
{"index": {"_id": "3"}}
{"title": "Natural Language Processing", "semantic_content": "NLP combines computational linguistics with machine learning to help computers understand human language", "category": "AI"}
'
```

## 🔗 Inference Integration

### Setting up Inference Endpoints

```bash
# Create inference endpoint for Hugging Face model
curl -X PUT "localhost:9200/_inference/text_embedding/my_embedding_model" -H 'Content-Type: application/json' -d'
{
  "service": "hugging_face",
  "service_settings": {
    "api_key": "your_hf_api_key",
    "url": "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
  },
  "task_settings": {
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  }
}
'

# Create inference endpoint for OpenAI
curl -X PUT "localhost:9200/_inference/text_embedding/openai_embeddings" -H 'Content-Type: application/json' -d'
{
  "service": "openai",
  "service_settings": {
    "api_key": "your_openai_api_key",
    "model_id": "text-embedding-3-small"
  }
}
'

# Create inference endpoint for Cohere
curl -X PUT "localhost:9200/_inference/text_embedding/cohere_embeddings" -H 'Content-Type: application/json' -d'
{
  "service": "cohere",
  "service_settings": {
    "api_key": "your_cohere_api_key",
    "model_id": "embed-english-v3.0"
  }
}
'
```

### Local Model Deployment

```bash
# Deploy local model using Elasticsearch ML
curl -X PUT "localhost:9200/_ml/trained_models/sentence_transformer" -H 'Content-Type: application/json' -d'
{
  "description": "Sentence transformer model for semantic search",
  "model_type": "pytorch",
  "model_id": "sentence-transformers__all-minilm-l6-v2",
  "inference_config": {
    "text_embedding": {
      "vocabulary": "...",
      "tokenization": {
        "type": "word_piece"
      }
    }
  }
}
'

# Start model deployment
curl -X POST "localhost:9200/_ml/trained_models/sentence_transformer/_start"

# Create inference endpoint for local model
curl -X PUT "localhost:9200/_inference/text_embedding/local_embeddings" -H 'Content-Type: application/json' -d'
{
  "service": "elasticsearch",
  "service_settings": {
    "num_allocations": 1,
    "num_threads": 2,
    "model_id": "sentence_transformer"
  }
}
'
```

## 🔍 Natural Language Queries

### Basic Semantic Search

```bash
# Simple semantic search
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "semantic": {
      "field": "semantic_content",
      "query": "How do neural networks learn from data?"
    }
  }
}
'
```

### Semantic Query with Filters

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "semantic": {
            "field": "semantic_content",
            "query": "explain artificial intelligence concepts"
          }
        }
      ],
      "filter": [
        {"term": {"category": "AI"}},
        {"range": {"publish_date": {"gte": "2023-01-01"}}}
      ]
    }
  }
}
'
```

### Multi-field Semantic Search

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {
          "semantic": {
            "field": "semantic_title",
            "query": "machine learning algorithms",
            "boost": 2.0
          }
        },
        {
          "semantic": {
            "field": "semantic_content", 
            "query": "machine learning algorithms",
            "boost": 1.0
          }
        }
      ]
    }
  }
}
'
```

### Semantic + Traditional Hybrid

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {
          "semantic": {
            "field": "semantic_content",
            "query": "deep learning neural networks",
            "boost": 1.5
          }
        },
        {
          "multi_match": {
            "query": "deep learning neural networks",
            "fields": ["title^2", "content"],
            "boost": 1.0
          }
        }
      ],
      "minimum_should_match": 1
    }
  }
}
'
```

## 🎯 Contextual Search

### Question-Answer Pairs

```bash
# Index Q&A pairs with semantic understanding
curl -X PUT "localhost:9200/qa_knowledge" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "question": {"type": "text"},
      "answer": {"type": "text"},
      "context": {"type": "text"},
      "semantic_qa": {
        "type": "semantic_text",
        "inference_id": "my_embedding_model"
      }
    }
  }
}
'

# Index with combined question-answer context
curl -X POST "localhost:9200/qa_knowledge/_doc/1" -H 'Content-Type: application/json' -d'
{
  "question": "How does Elasticsearch handle vector search?",
  "answer": "Elasticsearch uses dense vector fields and kNN search with HNSW algorithm for efficient semantic similarity matching.",
  "context": "Elasticsearch vector search implementation details",
  "semantic_qa": "Question: How does Elasticsearch handle vector search? Answer: Elasticsearch uses dense vector fields and kNN search with HNSW algorithm for efficient semantic similarity matching."
}
'
```

### Contextual Question Answering

```bash
curl -X POST "localhost:9200/qa_knowledge/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "semantic": {
      "field": "semantic_qa",
      "query": "What algorithm does Elasticsearch use for similarity search?"
    }
  },
  "_source": ["question", "answer", "context"],
  "size": 5
}
'
```

### Intent-based Search

```python
# Python implementation for intent-based search
from elasticsearch import Elasticsearch
from transformers import pipeline

class IntentBasedSearch:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
    def classify_intent(self, query):
        """Classify user query intent"""
        candidate_labels = [
            "product_search", 
            "technical_support", 
            "tutorial_request",
            "comparison_query",
            "troubleshooting"
        ]
        
        result = self.intent_classifier(query, candidate_labels)
        return result['labels'][0], result['scores'][0]
    
    def search_with_intent(self, query, index="knowledge_base"):
        """Search with intent-aware routing"""
        intent, confidence = self.classify_intent(query)
        
        # Adjust search strategy based on intent
        if intent == "product_search":
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "semantic": {
                                    "field": "semantic_content",
                                    "query": query
                                }
                            }
                        ],
                        "filter": [
                            {"term": {"type": "product"}}
                        ]
                    }
                }
            }
        elif intent == "technical_support":
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "semantic": {
                                    "field": "semantic_content",
                                    "query": query,
                                    "boost": 2.0
                                }
                            },
                            {
                                "match": {
                                    "tags": {
                                        "query": "troubleshooting support help",
                                        "boost": 1.5
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        else:
            # Default semantic search
            search_body = {
                "query": {
                    "semantic": {
                        "field": "semantic_content",
                        "query": query
                    }
                }
            }
        
        response = self.es.search(index=index, body=search_body)
        return {
            "intent": intent,
            "confidence": confidence,
            "results": response['hits']['hits']
        }

# Usage
searcher = IntentBasedSearch()
results = searcher.search_with_intent("How do I fix connection errors?")
print(f"Detected intent: {results['intent']} (confidence: {results['confidence']:.2f})")
```

## 🌐 Multilingual Semantic Search

### Cross-language Search Setup

```bash
# Setup multilingual semantic field
curl -X PUT "localhost:9200/multilingual_docs" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "content": {"type": "text"},
      "language": {"type": "keyword"},
      "semantic_content": {
        "type": "semantic_text",
        "inference_id": "multilingual_embeddings"  // Multilingual model
      }
    }
  }
}
'

# Index documents in different languages
curl -X POST "localhost:9200/multilingual_docs/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_id": "1"}}
{"title": "Machine Learning Basics", "content": "Machine learning enables computers to learn patterns", "language": "en", "semantic_content": "Machine learning enables computers to learn patterns"}
{"index": {"_id": "2"}}
{"title": "Aprendizaje Automático", "content": "El aprendizaje automático permite que las computadoras aprendan patrones", "language": "es", "semantic_content": "El aprendizaje automático permite que las computadoras aprendan patrones"}
{"index": {"_id": "3"}}
{"title": "機械学習の基礎", "content": "機械学習はコンピュータがパターンを学習することを可能にします", "language": "ja", "semantic_content": "機械学習はコンピュータがパターンを学習することを可能にします"}
'
```

### Cross-language Query

```bash
# Search in English, find results in any language
curl -X POST "localhost:9200/multilingual_docs/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "semantic": {
      "field": "semantic_content",
      "query": "artificial intelligence algorithms"
    }
  },
  "_source": ["title", "content", "language"]
}
'
```

## ⚡ Performance & Scaling

### Optimizing Semantic Search

```bash
# Optimize index settings for semantic search
curl -X PUT "localhost:9200/optimized_semantic" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "5s",
    "index.mapping.total_fields.limit": 2000
  },
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "content": {"type": "text"},
      "semantic_content": {
        "type": "semantic_text",
        "inference_id": "optimized_model",
        "model_settings": {
          "dimensions": 384,  // Balance between quality and performance
          "similarity": "cosine"
        }
      }
    }
  }
}
'
```

### Caching Strategies

```python
# Implement query result caching
import hashlib
import json
import time
from elasticsearch import Elasticsearch

class CachedSemanticSearch:
    def __init__(self, cache_ttl=3600):  # 1 hour TTL
        self.es = Elasticsearch(['http://localhost:9200'])
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    def _get_cache_key(self, query, filters=None):
        """Generate cache key for query"""
        cache_data = {
            'query': query,
            'filters': filters or {}
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def semantic_search(self, query, index="articles", filters=None, use_cache=True):
        """Cached semantic search"""
        cache_key = self._get_cache_key(query, filters)
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if (time.time() - timestamp) < self.cache_ttl:
                return cached_result
        
        # Build search query
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "semantic": {
                                "field": "semantic_content",
                                "query": query
                            }
                        }
                    ]
                }
            }
        }
        
        if filters:
            search_body["query"]["bool"]["filter"] = filters
        
        # Execute search
        response = self.es.search(index=index, body=search_body)
        
        # Cache result
        if use_cache:
            self.cache[cache_key] = (response, time.time())
        
        return response
```

### Batch Processing

```python
# Efficient batch processing for semantic indexing
import asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

class BatchSemanticProcessor:
    def __init__(self, batch_size=100):
        self.es = AsyncElasticsearch(['http://localhost:9200'])
        self.batch_size = batch_size
    
    async def process_documents(self, documents, index_name):
        """Process documents in batches for semantic indexing"""
        
        def doc_generator():
            for doc in documents:
                yield {
                    "_index": index_name,
                    "_source": {
                        "title": doc["title"],
                        "content": doc["content"],
                        "semantic_content": doc["content"],  # Will be processed by inference
                        "metadata": doc.get("metadata", {})
                    }
                }
        
        # Bulk index with async
        try:
            async for success, info in async_bulk(
                self.es,
                doc_generator(),
                chunk_size=self.batch_size,
                request_timeout=60
            ):
                if not success:
                    print(f"Failed to index: {info}")
                    
        except Exception as e:
            print(f"Bulk indexing error: {e}")
        
        await self.es.close()

# Usage
async def main():
    processor = BatchSemanticProcessor(batch_size=50)
    documents = [
        {"title": "Doc 1", "content": "Content 1"},
        {"title": "Doc 2", "content": "Content 2"},
        # ... more documents
    ]
    await processor.process_documents(documents, "semantic_index")

# Run async processing
asyncio.run(main())
```

## 🎯 Advanced Applications

### Conversational Search

```python
# Implement conversational search with context
class ConversationalSearch:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.conversation_history = {}
    
    def search_with_context(self, user_id, query, max_context=3):
        """Search with conversation context"""
        
        # Get conversation history
        history = self.conversation_history.get(user_id, [])
        
        # Build context-aware query
        context_queries = []
        if history:
            # Include recent conversation context
            recent_context = " ".join([h['query'] for h in history[-max_context:]])
            context_query = f"{recent_context} {query}"
        else:
            context_query = query
        
        # Perform semantic search
        response = self.es.search(
            index='knowledge_base',
            body={
                "query": {
                    "bool": {
                        "should": [
                            {
                                "semantic": {
                                    "field": "semantic_content",
                                    "query": context_query,
                                    "boost": 1.5
                                }
                            },
                            {
                                "semantic": {
                                    "field": "semantic_content", 
                                    "query": query,
                                    "boost": 1.0
                                }
                            }
                        ]
                    }
                }
            }
        )
        
        # Update conversation history
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            'query': query,
            'timestamp': time.time(),
            'results_count': len(response['hits']['hits'])
        })
        
        # Limit history size
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
        
        return response['hits']['hits']
```

### Smart Content Recommendations

```bash
# Content recommendation using semantic similarity
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must_not": [
        {"term": {"_id": "current_article_id"}}
      ],
      "must": [
        {
          "semantic": {
            "field": "semantic_content",
            "query": "machine learning artificial intelligence neural networks"
          }
        }
      ],
      "filter": [
        {"term": {"status": "published"}},
        {"range": {"publish_date": {"gte": "2023-01-01"}}}
      ]
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"popularity_score": {"order": "desc"}}
  ],
  "_source": ["title", "summary", "url", "publish_date"],
  "size": 5
}
'
```

### Semantic Faceted Search

```bash
# Combine semantic search with faceted navigation
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "semantic": {
            "field": "semantic_content",
            "query": "data science machine learning"
          }
        }
      ],
      "filter": [
        {"terms": {"category": ["AI", "Data Science"]}},
        {"range": {"publish_date": {"gte": "2023-01-01"}}}
      ]
    }
  },
  "aggs": {
    "categories": {
      "terms": {"field": "category"}
    },
    "authors": {
      "terms": {"field": "author.keyword"}
    },
    "semantic_topics": {
      "significant_terms": {
        "field": "tags",
        "size": 10
      }
    },
    "date_ranges": {
      "date_range": {
        "field": "publish_date",
        "ranges": [
          {"key": "Last 30 days", "from": "now-30d"},
          {"key": "Last 3 months", "from": "now-3M", "to": "now-30d"},
          {"key": "Older", "to": "now-3M"}
        ]
      }
    }
  }
}
'
```

## 🔗 Next Steps

Now that you've mastered semantic search, let's explore the modern query language:

1. **[ES|QL Basics](esql-basics.md)** - SQL-like query language for analytics
2. **[Performance Optimization](../06-performance-production/optimization-strategies.md)** - Scale your semantic search
3. **[Monitoring & Operations](../06-performance-production/monitoring-operations.md)** - Monitor semantic search performance

## 📚 Key Takeaways

- ✅ **Use semantic_text fields** for automatic embedding generation
- ✅ **Choose appropriate inference models** for your domain and language
- ✅ **Combine semantic and traditional search** for optimal results
- ✅ **Implement context awareness** for better user experiences
- ✅ **Cache frequently used queries** for performance
- ✅ **Consider multilingual capabilities** for global applications
- ✅ **Monitor model performance** and update as needed
- ✅ **Test semantic relevance** with real user queries

Ready to explore the modern query language? Continue with [ES|QL Basics](esql-basics.md) to learn SQL-like analytics capabilities!