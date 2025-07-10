# Relevance Scoring

**Master search result ranking and customize relevance for optimal user experience**

*Estimated reading time: 30 minutes*

## Overview

Relevance scoring determines how well documents match a search query and controls the order of search results. This guide covers Elasticsearch's scoring algorithms, relevance tuning techniques, and advanced scoring strategies for building exceptional search experiences.

## 📋 Table of Contents

1. [Scoring Fundamentals](#scoring-fundamentals)
2. [TF-IDF and BM25](#tf-idf-and-bm25)
3. [Function Score Queries](#function-score-queries)
4. [Boosting Strategies](#boosting-strategies)
5. [Custom Scoring](#custom-scoring)
6. [Relevance Testing](#relevance-testing)
7. [Advanced Techniques](#advanced-techniques)

## 🎯 Scoring Fundamentals

### Understanding the _score Field

Every search result includes a `_score` field representing relevance:

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"title": "elasticsearch tutorial"}
  }
}
'
```

**Response with scores:**
```json
{
  "hits": {
    "max_score": 2.4159274,
    "hits": [
      {
        "_id": "1",
        "_score": 2.4159274,
        "_source": {"title": "Elasticsearch Tutorial for Beginners"}
      },
      {
        "_id": "2", 
        "_score": 1.8739285,
        "_source": {"title": "Advanced Elasticsearch Techniques"}
      }
    ]
  }
}
```

### Explain API

Understand how scores are calculated:

```bash
curl -X POST "localhost:9200/articles/_explain/1" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"title": "elasticsearch tutorial"}
  }
}
'
```

**Explanation breakdown:**
```json
{
  "matched": true,
  "explanation": {
    "value": 2.4159274,
    "description": "sum of:",
    "details": [
      {
        "value": 1.2039728,
        "description": "weight(title:elasticsearch in 0)",
        "details": [
          {
            "value": 1.2039728,
            "description": "score(freq=1.0), computed from:",
            "details": [
              {"value": 2.2, "description": "boost"},
              {"value": 0.2876821, "description": "idf"},
              {"value": 1.0, "description": "tf"}
            ]
          }
        ]
      }
    ]
  }
}
```

## 📊 TF-IDF and BM25

### TF-IDF (Classic Scoring)

**Term Frequency-Inverse Document Frequency:**
- **TF**: How often a term appears in a document
- **IDF**: How rare the term is across all documents
- **Score**: TF × IDF × field boost × query boost

### BM25 (Default in Elasticsearch)

BM25 improves on TF-IDF with saturation:

```bash
# Configure BM25 parameters
curl -X PUT "localhost:9200/articles" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index": {
      "similarity": {
        "custom_bm25": {
          "type": "BM25",
          "k1": 1.2,      // Term frequency saturation point
          "b": 0.75       // Field length normalization factor
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "similarity": "custom_bm25"
      },
      "content": {
        "type": "text",
        "similarity": "BM25"
      }
    }
  }
}
'
```

**BM25 Parameters:**
- **k1** (1.2): Controls term frequency saturation. Higher = less saturation
- **b** (0.75): Controls field length normalization. 0 = no normalization, 1 = full normalization

### Custom Similarity

```bash
curl -X PUT "localhost:9200/articles" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index": {
      "similarity": {
        "title_similarity": {
          "type": "BM25",
          "k1": 1.6,    // Higher for title fields (less saturation)
          "b": 0.1      // Lower for title fields (less length normalization)
        },
        "content_similarity": {
          "type": "BM25", 
          "k1": 1.2,    // Standard for content
          "b": 0.75     // Standard normalization
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "similarity": "title_similarity"
      },
      "content": {
        "type": "text", 
        "similarity": "content_similarity"
      }
    }
  }
}
'
```

## ⚡ Function Score Queries

Modify scores based on document properties beyond text relevance.

### Basic Function Score

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"content": "elasticsearch"}
      },
      "boost": 1.0,
      "functions": [
        {
          "field_value_factor": {
            "field": "popularity",
            "factor": 0.1,
            "modifier": "log1p",
            "missing": 0
          }
        }
      ],
      "score_mode": "sum",      // How to combine function scores
      "boost_mode": "multiply"  // How to combine with query score
    }
  }
}
'
```

### Field Value Factor

Boost based on numeric field values:

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"title": "elasticsearch"}
      },
      "functions": [
        {
          "field_value_factor": {
            "field": "view_count",
            "factor": 0.01,
            "modifier": "sqrt",      // Options: none, log, log1p, log2p, ln, ln1p, ln2p, square, sqrt, reciprocal
            "missing": 1
          }
        },
        {
          "field_value_factor": {
            "field": "like_count", 
            "factor": 0.05,
            "modifier": "log1p"
          }
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply",
      "max_boost": 3.0  // Cap the maximum boost
    }
  }
}
'
```

### Decay Functions

Apply distance-based scoring:

**Linear Decay:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"content": "elasticsearch"}
      },
      "functions": [
        {
          "linear": {
            "publish_date": {
              "origin": "now",
              "scale": "30d",
              "offset": "7d",
              "decay": 0.5
            }
          }
        }
      ],
      "boost_mode": "multiply"
    }
  }
}
'
```

**Exponential Decay:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"content": "tutorial"}
      },
      "functions": [
        {
          "exp": {
            "publish_date": {
              "origin": "now",
              "scale": "14d",      // Half-life of decay
              "offset": "3d",      // No decay within 3 days
              "decay": 0.5         // Decay factor at scale distance
            }
          }
        }
      ]
    }
  }
}
'
```

**Gaussian Decay:**
```bash
curl -X POST "localhost:9200/stores/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"name": "coffee"}
      },
      "functions": [
        {
          "gauss": {
            "location": {
              "origin": {"lat": 40.7128, "lon": -74.0060},
              "scale": "5km",
              "offset": "1km",
              "decay": 0.33
            }
          }
        }
      ]
    }
  }
}
'
```

### Random Score

Add randomization while maintaining relevance:

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"category": "technology"}
      },
      "functions": [
        {
          "random_score": {
            "seed": 12345,  // Use user ID for consistent randomization
            "field": "_seq_no"
          },
          "weight": 0.5
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply"
    }
  }
}
'
```

### Script Score

Custom scoring logic:

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"content": "elasticsearch"}
      },
      "script_score": {
        "script": {
          "source": "Math.log(2 + doc['\''view_count'\''].value) * params.factor + Math.sqrt(doc['\''like_count'\''].value)",
          "params": {
            "factor": 1.5
          }
        }
      }
    }
  }
}
'
```

## 🚀 Boosting Strategies

### Query-time Boosting

**Field Boosting:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "fields": [
        "title^3",        // Title 3x more important
        "summary^2",      // Summary 2x more important
        "content^1",      // Content base weight
        "tags^1.5"       // Tags 1.5x more important
      ]
    }
  }
}
'
```

**Term-level Boosting:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {
          "match": {
            "title": {
              "query": "elasticsearch",
              "boost": 3.0
            }
          }
        },
        {
          "match": {
            "content": {
              "query": "elasticsearch",
              "boost": 1.0
            }
          }
        }
      ]
    }
  }
}
'
```

### Index-time Boosting

**Document-level Boost:**
```bash
# Boost important documents at index time
curl -X POST "localhost:9200/articles/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Official Elasticsearch Guide",
  "content": "The official guide to Elasticsearch...",
  "_boost": 2.0  // Deprecated in newer versions
}
'
```

**Norm Disabling for Consistent Boosting:**
```bash
curl -X PUT "localhost:9200/articles" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "norms": false  // Disable length normalization
      }
    }
  }
}
'
```

### Negative Boosting

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "boosting": {
      "positive": {
        "match": {"content": "elasticsearch"}
      },
      "negative": {
        "multi_match": {
          "query": "deprecated old version outdated",
          "fields": ["content", "tags"]
        }
      },
      "negative_boost": 0.2  // Reduce score by 80%
    }
  }
}
'
```

## 🎨 Custom Scoring

### Script Score Query

Complete control over scoring:

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "script_score": {
      "query": {
        "match": {"content": "elasticsearch"}
      },
      "script": {
        "source": """
          double baseScore = _score;
          double popularityScore = Math.log(2 + doc['view_count'].value) * 0.1;
          double freshnessScore = Math.max(0, 1 - (System.currentTimeMillis() - doc['publish_date'].value.millis) / (86400000.0 * 365));
          double authorityScore = doc['author_rank'].value * 0.05;
          
          return baseScore * (1 + popularityScore + freshnessScore + authorityScore);
        """,
        "params": {
          "popularity_factor": 0.1,
          "freshness_weight": 0.2
        }
      }
    }
  }
}
'
```

### Conditional Scoring

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "script_score": {
      "query": {"match_all": {}},
      "script": {
        "source": """
          double score = _score;
          
          // Boost featured articles
          if (doc['featured'].value) {
            score *= 2.0;
          }
          
          // Boost recent articles
          long ageInDays = (System.currentTimeMillis() - doc['publish_date'].value.millis) / 86400000;
          if (ageInDays < 30) {
            score *= 1.5;
          } else if (ageInDays < 90) {
            score *= 1.2;
          }
          
          // Penalize short articles
          if (doc['word_count'].value < 500) {
            score *= 0.8;
          }
          
          return score;
        """
      }
    }
  }
}
'
```

### Personalized Scoring

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "script_score": {
      "query": {
        "match": {"content": "machine learning"}
      },
      "script": {
        "source": """
          double baseScore = _score;
          double personalityBoost = 1.0;
          
          // Boost based on user preferences
          if (params.user_categories.contains(doc['category'].value)) {
            personalityBoost += 0.5;
          }
          
          if (params.user_authors.contains(doc['author'].value)) {
            personalityBoost += 0.3;
          }
          
          // Boost based on reading history similarity
          double topicScore = 0;
          for (tag in doc['tags']) {
            if (params.user_interests.containsKey(tag.value)) {
              topicScore += params.user_interests[tag.value];
            }
          }
          
          return baseScore * personalityBoost * (1 + topicScore);
        """,
        "params": {
          "user_categories": ["technology", "programming"],
          "user_authors": ["john_doe", "jane_smith"],
          "user_interests": {
            "elasticsearch": 0.8,
            "data_science": 0.6,
            "machine_learning": 0.9
          }
        }
      }
    }
  }
}
'
```

## 🧪 Relevance Testing

### A/B Testing Framework

```bash
# Version A: Standard relevance
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "fields": ["title^2", "content"]
    }
  },
  "size": 10
}
'

# Version B: Enhanced relevance  
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "multi_match": {
          "query": "elasticsearch tutorial",
          "fields": ["title^3", "content^1", "tags^2"]
        }
      },
      "functions": [
        {
          "field_value_factor": {
            "field": "view_count",
            "factor": 0.01,
            "modifier": "log1p"
          }
        }
      ],
      "boost_mode": "multiply"
    }
  },
  "size": 10
}
'
```

### Relevance Metrics

**Precision at K:**
```javascript
// Calculate precision@10
function precisionAtK(results, relevantDocs, k) {
  const topK = results.slice(0, k);
  const relevantInTopK = topK.filter(doc => relevantDocs.includes(doc.id));
  return relevantInTopK.length / k;
}
```

**Mean Reciprocal Rank:**
```javascript
function meanReciprocalRank(queries) {
  let sum = 0;
  for (const query of queries) {
    for (let i = 0; i < query.results.length; i++) {
      if (query.relevantDocs.includes(query.results[i].id)) {
        sum += 1 / (i + 1);
        break;
      }
    }
  }
  return sum / queries.length;
}
```

### Rank Evaluation API

```bash
# Evaluate ranking quality
curl -X POST "localhost:9200/_rank_eval" -H 'Content-Type: application/json' -d'
{
  "requests": [
    {
      "id": "elasticsearch_tutorial",
      "request": {
        "query": {
          "match": {"title": "elasticsearch tutorial"}
        }
      },
      "ratings": [
        {"_index": "articles", "_id": "1", "rating": 3},
        {"_index": "articles", "_id": "2", "rating": 2},
        {"_index": "articles", "_id": "3", "rating": 1}
      ]
    }
  ],
  "metric": {
    "precision": {
      "k": 10,
      "relevant_rating_threshold": 2
    }
  }
}
'
```

## 🎯 Advanced Techniques

### Learning to Rank

```bash
# Use external ML model scores
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "script_score": {
      "query": {
        "match": {"content": "elasticsearch"}
      },
      "script": {
        "source": """
          // Extract features
          Map features = new HashMap();
          features.put("tf_score", _score);
          features.put("view_count", doc['view_count'].value);
          features.put("like_count", doc['like_count'].value);
          features.put("comment_count", doc['comment_count'].value);
          features.put("freshness", Math.max(0, 1 - (System.currentTimeMillis() - doc['publish_date'].value.millis) / (86400000.0 * 365)));
          
          // Apply learned weights (from external ML model)
          double score = features.get("tf_score") * params.weights.tf_weight +
                        Math.log(1 + features.get("view_count")) * params.weights.view_weight +
                        Math.log(1 + features.get("like_count")) * params.weights.like_weight +
                        features.get("freshness") * params.weights.freshness_weight;
                        
          return Math.max(0, score);
        """,
        "params": {
          "weights": {
            "tf_weight": 1.0,
            "view_weight": 0.15,
            "like_weight": 0.25,
            "freshness_weight": 0.8
          }
        }
      }
    }
  }
}
'
```

### Contextual Scoring

```bash
# Time-aware scoring
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "script_score": {
      "query": {
        "bool": {
          "must": [
            {"match": {"content": "coronavirus"}}
          ]
        }
      },
      "script": {
        "source": """
          double baseScore = _score;
          long currentTime = System.currentTimeMillis();
          long docTime = doc['publish_date'].value.millis;
          long timeDiff = currentTime - docTime;
          
          // Different decay rates for different topics
          double decayRate;
          if (doc['category'].value.equals("news")) {
            decayRate = 0.1;  // News decays quickly
          } else if (doc['category'].value.equals("technology")) {
            decayRate = 0.05; // Tech content decays slower
          } else {
            decayRate = 0.02; // Evergreen content decays slowly
          }
          
          double timeScore = Math.exp(-decayRate * timeDiff / 86400000.0);
          return baseScore * timeScore;
        """
      }
    }
  }
}
'
```

### Multi-criteria Scoring

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "multi_match": {
          "query": "machine learning",
          "fields": ["title^2", "content"]
        }
      },
      "functions": [
        {
          "filter": {"range": {"view_count": {"gte": 1000}}},
          "weight": 1.5
        },
        {
          "filter": {"term": {"featured": true}},
          "weight": 2.0
        },
        {
          "exp": {
            "publish_date": {
              "origin": "now",
              "scale": "30d",
              "decay": 0.5
            }
          },
          "weight": 0.8
        },
        {
          "field_value_factor": {
            "field": "authority_score",
            "factor": 0.1,
            "modifier": "sqrt"
          }
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply",
      "min_score": 0.5
    }
  }
}
'
```

## 🔗 Next Steps

Now that you've mastered relevance scoring, let's explore modern search capabilities:

1. **[Vector Search](../05-modern-capabilities/vector-search.md)** - Semantic similarity search
2. **[Semantic Search](../05-modern-capabilities/semantic-search.md)** - Natural language understanding
3. **[Performance Optimization](../06-performance-production/optimization-strategies.md)** - Scale your relevance tuning

## 📚 Key Takeaways

- ✅ **Understand BM25 parameters** for your content characteristics
- ✅ **Use function_score** to incorporate business logic into relevance
- ✅ **Test different boosting strategies** with real user queries
- ✅ **Implement relevance testing** to measure search quality
- ✅ **Consider user context** in personalized scoring
- ✅ **Monitor and iterate** on relevance tuning
- ✅ **Balance text relevance** with other signals appropriately
- ✅ **Use script_score** for complex custom logic

Ready to explore modern search capabilities? Continue with [Vector Search](../05-modern-capabilities/vector-search.md) to learn about semantic similarity!