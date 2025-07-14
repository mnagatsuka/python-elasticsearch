# Vector Search

**Implement semantic similarity search with dense vectors and AI-powered embeddings**

*Estimated reading time: 40 minutes*

## Overview

Vector search enables semantic similarity matching by representing text, images, and other data as high-dimensional vectors. This guide covers dense vector fields, k-nearest neighbor (kNN) search, hybrid search combining traditional and vector approaches, and integration with machine learning models.

## 📋 Table of Contents

1. [Vector Search Fundamentals](#vector-search-fundamentals)
2. [Dense Vector Fields](#dense-vector-fields)
3. [kNN Search](#knn-search)
4. [Hybrid Search](#hybrid-search)
5. [Embedding Generation](#embedding-generation)
6. [Performance Optimization](#performance-optimization)
7. [Real-world Applications](#real-world-applications)

## 🧠 Vector Search Fundamentals

### What is Vector Search?

Vector search finds similar items by comparing their mathematical representations (embeddings) in multi-dimensional space. Unlike traditional text search that matches keywords, vector search understands semantic meaning.

**Traditional Search:**
- Query: "car" → Matches: documents containing "car"
- Misses: "automobile", "vehicle", "auto"

**Vector Search:**
- Query: "car" → Matches: semantically similar concepts
- Finds: "automobile", "vehicle", "transportation", "SUV"

### Use Cases

- **Semantic Search**: Find conceptually similar content
- **Recommendation Systems**: Suggest similar products/content
- **Question Answering**: Match questions to relevant answers
- **Image Search**: Find visually similar images
- **Anomaly Detection**: Identify outliers in vector space

### Vector Similarity Metrics

```bash
# Distance metrics supported in Elasticsearch
- cosine: Cosine similarity (default, range 0-2)
- dot_product: Dot product (range depends on vectors)
- l2_norm: Euclidean distance
- l1_norm: Manhattan distance
```

## 📊 Dense Vector Fields

### Basic Vector Field Mapping

```bash
curl -X PUT "localhost:9200/documents" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "content": {"type": "text"},
      "title_vector": {
        "type": "dense_vector",
        "dims": 384,
        "similarity": "cosine"
      },
      "content_vector": {
        "type": "dense_vector",
        "dims": 768,
        "similarity": "cosine"
      }
    }
  }
}
'
```

### Vector Field Parameters

```json
{
  "vector_field": {
    "type": "dense_vector",
    "dims": 384,                    // Vector dimensions (required)
    "similarity": "cosine",         // Similarity metric
    "index": true,                  // Enable indexing for fast search
    "index_options": {
      "type": "hnsw",              // Hierarchical Navigable Small World
      "m": 16,                     // Number of connections
      "ef_construction": 200       // Size of candidate list during indexing
    }
  }
}
```

### Indexing Documents with Vectors

```bash
# Index document with pre-computed vectors
curl -X POST "localhost:9200/documents/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Introduction to Machine Learning",
  "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
  "title_vector": [0.1, -0.2, 0.8, 0.3, ...],  // 384-dimensional vector
  "content_vector": [0.05, 0.12, -0.34, ...]   // 768-dimensional vector
}
'

# Bulk indexing with vectors
curl -X POST "localhost:9200/documents/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_id": "2"}}
{"title": "Deep Learning Fundamentals", "content": "Deep learning uses neural networks with multiple layers", "title_vector": [0.2, -0.1, 0.9, 0.4, ...], "content_vector": [0.08, 0.15, -0.28, ...]}
{"index": {"_id": "3"}}
{"title": "Natural Language Processing", "content": "NLP combines computational linguistics with machine learning", "title_vector": [0.15, -0.25, 0.7, 0.35, ...], "content_vector": [0.06, 0.18, -0.31, ...]}
'
```

## 🔍 kNN Search

### Basic kNN Query

```bash
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "knn": {
    "field": "content_vector",
    "query_vector": [0.05, 0.12, -0.34, 0.22, ...],
    "k": 10,
    "num_candidates": 50
  },
  "_source": ["title", "content"]
}
'
```

### kNN Parameters

```json
{
  "knn": {
    "field": "content_vector",           // Vector field name
    "query_vector": [...],               // Query vector
    "k": 10,                            // Number of results to return
    "num_candidates": 50,               // Candidates to examine (≥ k)
    "filter": {                         // Optional filter
      "term": {"category": "technology"}
    },
    "boost": 1.5                        // Boost kNN scores
  }
}
```

### kNN with Filters

```bash
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "knn": {
    "field": "content_vector",
    "query_vector": [0.05, 0.12, -0.34, ...],
    "k": 10,
    "num_candidates": 100,
    "filter": {
      "bool": {
        "must": [
          {"term": {"status": "published"}},
          {"range": {"publish_date": {"gte": "2023-01-01"}}}
        ]
      }
    }
  }
}
'
```

### Multiple kNN Queries

```bash
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "knn": [
    {
      "field": "title_vector",
      "query_vector": [0.1, -0.2, 0.8, ...],
      "k": 5,
      "num_candidates": 25,
      "boost": 2.0
    },
    {
      "field": "content_vector", 
      "query_vector": [0.05, 0.12, -0.34, ...],
      "k": 5,
      "num_candidates": 25,
      "boost": 1.0
    }
  ]
}
'
```

## 🔄 Hybrid Search

Combine traditional text search with vector search for optimal results.

### Query + kNN Combination

```bash
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "machine learning algorithms",
            "fields": ["title^2", "content"],
            "boost": 1.0
          }
        }
      ]
    }
  },
  "knn": {
    "field": "content_vector",
    "query_vector": [0.05, 0.12, -0.34, ...],
    "k": 10,
    "num_candidates": 50,
    "boost": 1.5
  },
  "size": 10
}
'
```

### Rank Fusion

Combine multiple ranking signals:

```bash
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "artificial intelligence",
            "fields": ["title^3", "content"]
          }
        }
      ]
    }
  },
  "knn": {
    "field": "content_vector",
    "query_vector": [0.1, -0.2, 0.8, ...],
    "k": 20,
    "num_candidates": 100
  },
  "rank": {
    "rrf": {
      "window_size": 50,
      "rank_constant": 20
    }
  }
}
'
```

### Weighted Hybrid Search

```bash
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "bool": {
          "should": [
            {
              "multi_match": {
                "query": "deep learning",
                "fields": ["title^2", "content"],
                "boost": 0.7
              }
            }
          ]
        }
      },
      "functions": [
        {
          "script_score": {
            "script": {
              "source": """
                // Add kNN similarity score
                double knnScore = 0;
                if (params.query_vector != null && doc['content_vector'].size() > 0) {
                  double[] queryVec = params.query_vector;
                  double[] docVec = doc['content_vector'].vectorValue();
                  
                  double dotProduct = 0;
                  double queryMag = 0;
                  double docMag = 0;
                  
                  for (int i = 0; i < Math.min(queryVec.length, docVec.length); i++) {
                    dotProduct += queryVec[i] * docVec[i];
                    queryMag += queryVec[i] * queryVec[i];
                    docMag += docVec[i] * docVec[i];
                  }
                  
                  if (queryMag > 0 && docMag > 0) {
                    knnScore = dotProduct / (Math.sqrt(queryMag) * Math.sqrt(docMag));
                  }
                }
                
                return _score + (knnScore * params.vector_weight);
              """,
              "params": {
                "query_vector": [0.1, -0.2, 0.8, ...],
                "vector_weight": 1.3
              }
            }
          }
        }
      ]
    }
  }
}
'
```

## 🤖 Embedding Generation

### Using Sentence Transformers (Python)

```python
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

# Initialize model and Elasticsearch
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
es = Elasticsearch(['http://localhost:9200'])

def generate_embeddings(texts):
    """Generate embeddings for a list of texts"""
    embeddings = model.encode(texts)
    return embeddings.tolist()

def index_document_with_vectors(doc_id, title, content):
    """Index document with generated vectors"""
    
    # Generate embeddings
    title_vector = generate_embeddings([title])[0]
    content_vector = generate_embeddings([content])[0]
    
    # Index document
    doc = {
        'title': title,
        'content': content,
        'title_vector': title_vector,
        'content_vector': content_vector
    }
    
    es.index(index='documents', id=doc_id, body=doc)

# Example usage
index_document_with_vectors(
    doc_id='1',
    title='Introduction to Vector Search',
    content='Vector search enables semantic similarity matching using dense embeddings'
)

def search_similar_documents(query_text, k=10):
    """Search for similar documents using vector similarity"""
    
    # Generate query vector
    query_vector = generate_embeddings([query_text])[0]
    
    # Perform kNN search
    response = es.search(
        index='documents',
        body={
            'knn': {
                'field': 'content_vector',
                'query_vector': query_vector,
                'k': k,
                'num_candidates': k * 5
            },
            '_source': ['title', 'content']
        }
    )
    
    return response['hits']['hits']

# Search example
results = search_similar_documents('semantic search with embeddings')
for hit in results:
    print(f"Score: {hit['_score']:.4f}")
    print(f"Title: {hit['_source']['title']}")
    print(f"Content: {hit['_source']['content'][:100]}...")
    print()
```

### Using OpenAI Embeddings

```python
import openai
from elasticsearch import Elasticsearch

openai.api_key = 'your-api-key'
es = Elasticsearch(['http://localhost:9200'])

def get_openai_embedding(text, model="text-embedding-3-small"):
    """Generate embedding using OpenAI API"""
    response = openai.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def index_with_openai_embeddings(doc_id, title, content):
    """Index document with OpenAI embeddings"""
    
    # Generate embeddings
    title_vector = get_openai_embedding(title)
    content_vector = get_openai_embedding(content)
    
    doc = {
        'title': title,
        'content': content,
        'title_vector': title_vector,
        'content_vector': content_vector
    }
    
    es.index(index='documents', id=doc_id, body=doc)

def hybrid_search(query_text, k=10):
    """Combine text and vector search"""
    
    query_vector = get_openai_embedding(query_text)
    
    response = es.search(
        index='documents',
        body={
            'query': {
                'bool': {
                    'should': [
                        {
                            'multi_match': {
                                'query': query_text,
                                'fields': ['title^2', 'content'],
                                'boost': 1.0
                            }
                        }
                    ]
                }
            },
            'knn': {
                'field': 'content_vector',
                'query_vector': query_vector,
                'k': k,
                'num_candidates': k * 3,
                'boost': 1.5
            }
        }
    )
    
    return response['hits']['hits']
```

### Ingest Pipeline with ML Model

```bash
# Create ingest pipeline with text embedding processor
curl -X PUT "localhost:9200/_ingest/pipeline/text_embeddings" -H 'Content-Type: application/json' -d'
{
  "description": "Generate embeddings for text fields",
  "processors": [
    {
      "inference": {
        "model_id": "sentence-transformers__all-minilm-l6-v2",
        "target_field": "ml",
        "field_map": {
          "content": "text_field"
        }
      }
    },
    {
      "set": {
        "field": "content_vector",
        "value": "{{ml.predicted_value}}"
      }
    },
    {
      "remove": {
        "field": "ml"
      }
    }
  ]
}
'

# Index documents through pipeline
curl -X POST "localhost:9200/documents/_doc/1?pipeline=text_embeddings" -H 'Content-Type: application/json' -d'
{
  "title": "Elasticsearch Vector Search",
  "content": "Vector search provides semantic similarity matching capabilities"
}
'
```

## ⚡ Performance Optimization

### HNSW Index Tuning

```bash
curl -X PUT "localhost:9200/optimized_vectors" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "content_vector": {
        "type": "dense_vector",
        "dims": 384,
        "similarity": "cosine",
        "index": true,
        "index_options": {
          "type": "hnsw",
          "m": 32,                    // Higher m = better recall, more memory
          "ef_construction": 400      // Higher ef = better recall, slower indexing
        }
      }
    }
  },
  "settings": {
    "index": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "knn_algorithm_parameter_ef_search": 100  // Search-time parameter
    }
  }
}
'
```

### Search-time Optimization

```bash
# Optimize num_candidates based on k
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "knn": {
    "field": "content_vector",
    "query_vector": [...],
    "k": 10,
    "num_candidates": 50  // Rule of thumb: 5-10x k value
  }
}
'

# Use filters to reduce search space
curl -X POST "localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'
{
  "knn": {
    "field": "content_vector",
    "query_vector": [...],
    "k": 10,
    "num_candidates": 100,
    "filter": {
      "bool": {
        "must": [
          {"term": {"category": "technology"}},
          {"range": {"publish_date": {"gte": "2024-01-01"}}}
        ]
      }
    }
  }
}
'
```

### Memory Considerations

```bash
# Estimate memory usage
# Formula: (number_of_vectors × dimensions × 4 bytes) + HNSW_overhead
# HNSW overhead ≈ number_of_vectors × m × 4 bytes

# Example: 1M vectors, 384 dimensions, m=16
# Vector storage: 1,000,000 × 384 × 4 = 1.5GB
# HNSW overhead: 1,000,000 × 16 × 4 = 64MB
# Total ≈ 1.6GB per shard
```

## 🎯 Real-world Applications

### E-commerce Product Recommendations

```bash
# Create product vectors index
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "name": {"type": "text"},
      "description": {"type": "text"},
      "category": {"type": "keyword"},
      "price": {"type": "float"},
      "brand": {"type": "keyword"},
      "description_vector": {
        "type": "dense_vector",
        "dims": 384,
        "similarity": "cosine"
      },
      "visual_vector": {
        "type": "dense_vector", 
        "dims": 512,
        "similarity": "cosine"
      }
    }
  }
}
'

# Find similar products
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"category": "electronics"}},
        {"range": {"price": {"gte": 100, "lte": 1000}}}
      ]
    }
  },
  "knn": {
    "field": "description_vector",
    "query_vector": [0.1, -0.2, 0.8, ...],  // Vector of viewed product
    "k": 20,
    "num_candidates": 100
  },
  "size": 10
}
'
```

### Document Search & Retrieval

```python
# RAG (Retrieval-Augmented Generation) implementation
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

class DocumentRetriever:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def retrieve_relevant_docs(self, question, k=5):
        """Retrieve documents relevant to a question"""
        
        # Generate question embedding
        question_vector = self.model.encode([question])[0].tolist()
        
        # Hybrid search: text + vector
        response = self.es.search(
            index='knowledge_base',
            body={
                'query': {
                    'bool': {
                        'should': [
                            {
                                'multi_match': {
                                    'query': question,
                                    'fields': ['title^2', 'content'],
                                    'boost': 0.3
                                }
                            }
                        ]
                    }
                },
                'knn': {
                    'field': 'content_vector',
                    'query_vector': question_vector,
                    'k': k * 2,
                    'num_candidates': k * 5,
                    'boost': 0.7
                },
                'size': k,
                '_source': ['title', 'content', 'url']
            }
        )
        
        return [hit['_source'] for hit in response['hits']['hits']]
    
    def semantic_search(self, query, filters=None):
        """Perform semantic search with optional filters"""
        
        query_vector = self.model.encode([query])[0].tolist()
        
        search_body = {
            'knn': {
                'field': 'content_vector',
                'query_vector': query_vector,
                'k': 10,
                'num_candidates': 50
            }
        }
        
        if filters:
            search_body['knn']['filter'] = filters
        
        response = self.es.search(index='knowledge_base', body=search_body)
        return response['hits']['hits']

# Usage example
retriever = DocumentRetriever()

# Retrieve documents for RAG
question = "How does vector search work in Elasticsearch?"
relevant_docs = retriever.retrieve_relevant_docs(question)

# Semantic search with filters
results = retriever.semantic_search(
    "machine learning algorithms",
    filters={
        "bool": {
            "must": [
                {"term": {"category": "ai"}},
                {"range": {"publish_date": {"gte": "2023-01-01"}}}
            ]
        }
    }
)
```

### Content-based Image Search

```python
# Image similarity search using CLIP embeddings
import torch
import clip
from PIL import Image
from elasticsearch import Elasticsearch

class ImageSearchEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        self.es = Elasticsearch(['http://localhost:9200'])
    
    def generate_image_embedding(self, image_path):
        """Generate CLIP embedding for an image"""
        image = Image.open(image_path)
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy()[0].tolist()
    
    def generate_text_embedding(self, text):
        """Generate CLIP embedding for text"""
        text_input = clip.tokenize([text]).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text_input)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        return text_features.cpu().numpy()[0].tolist()
    
    def search_similar_images(self, query_image_path, k=10):
        """Find visually similar images"""
        query_vector = self.generate_image_embedding(query_image_path)
        
        response = self.es.search(
            index='images',
            body={
                'knn': {
                    'field': 'image_vector',
                    'query_vector': query_vector,
                    'k': k,
                    'num_candidates': k * 3
                },
                '_source': ['filename', 'url', 'caption']
            }
        )
        
        return response['hits']['hits']
    
    def search_images_by_text(self, text_query, k=10):
        """Find images matching text description"""
        query_vector = self.generate_text_embedding(text_query)
        
        response = self.es.search(
            index='images',
            body={
                'knn': {
                    'field': 'image_vector',
                    'query_vector': query_vector,
                    'k': k,
                    'num_candidates': k * 3
                }
            }
        )
        
        return response['hits']['hits']

# Usage
search_engine = ImageSearchEngine()

# Find similar images
similar_images = search_engine.search_similar_images('/path/to/query_image.jpg')

# Find images by text description
results = search_engine.search_images_by_text("a cat sitting on a red sofa")
```

### Question Answering System

```bash
# Q&A knowledge base with vector search
curl -X PUT "localhost:9200/qa_pairs" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "question": {"type": "text"},
      "answer": {"type": "text"},
      "category": {"type": "keyword"},
      "question_vector": {
        "type": "dense_vector",
        "dims": 384,
        "similarity": "cosine"
      }
    }
  }
}
'

# Search for similar questions
curl -X POST "localhost:9200/qa_pairs/_search" -H 'Content-Type: application/json' -d'
{
  "knn": {
    "field": "question_vector",
    "query_vector": [0.1, -0.2, 0.8, ...],  // Encoded user question
    "k": 5,
    "num_candidates": 25,
    "filter": {
      "term": {"category": "elasticsearch"}
    }
  },
  "_source": ["question", "answer"]
}
'
```

## 🔗 Next Steps

Now that you've mastered vector search, let's explore semantic search capabilities:

1. **[Semantic Search](semantic-search.md)** - Natural language understanding and processing
2. **[ES|QL Basics](esql-basics.md)** - SQL-like query language for modern analytics
3. **[Performance Optimization](../06-performance-production/optimization-strategies.md)** - Scale your vector search implementation

## 📚 Key Takeaways

- ✅ **Choose appropriate vector dimensions** based on your model and use case
- ✅ **Optimize HNSW parameters** for your recall/performance requirements
- ✅ **Use hybrid search** to combine semantic and lexical matching
- ✅ **Implement proper embedding generation** pipelines
- ✅ **Consider memory requirements** for large vector datasets
- ✅ **Filter vector searches** to improve performance and relevance
- ✅ **Test different similarity metrics** for your specific domain
- ✅ **Monitor vector search performance** and tune accordingly

Ready to dive deeper into semantic capabilities? Continue with [Semantic Search](semantic-search.md) to learn about natural language understanding!