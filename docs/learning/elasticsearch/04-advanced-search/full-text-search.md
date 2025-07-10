# Full-text Search

**Master advanced text analysis and search patterns for optimal search experiences**

*Estimated reading time: 35 minutes*

## Overview

Full-text search is Elasticsearch's core strength. This guide covers advanced text analysis, search patterns, relevance tuning, and techniques for building sophisticated search experiences that understand language nuances and user intent.

## 📋 Table of Contents

1. [Text Analysis Deep Dive](#text-analysis-deep-dive)
2. [Advanced Query Patterns](#advanced-query-patterns)
3. [Relevance Tuning](#relevance-tuning)
4. [Language-specific Search](#language-specific-search)
5. [Search-as-you-type](#search-as-you-type)
6. [Fuzzy and Phonetic Search](#fuzzy-and-phonetic-search)
7. [Performance Optimization](#performance-optimization)

## 🔬 Text Analysis Deep Dive

### Understanding Analyzers

Analyzers are the foundation of full-text search, transforming text into searchable tokens:

```bash
# Test different analyzers
curl -X POST "localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "standard",
  "text": "The Quick Brown Fox Jumps Over the Lazy Dog!"
}
'

# Response: ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
```

### Built-in Analyzers

**Standard Analyzer:**
```bash
curl -X POST "localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "standard",
  "text": "Fast Wi-Fi setup @ home (2024)"
}
'
# Output: ["fast", "wi", "fi", "setup", "home", "2024"]
```

**English Analyzer:**
```bash
curl -X POST "localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "english",
  "text": "The dogs are running quickly"
}
'
# Output: ["dog", "run", "quickli"] - note stemming
```

**Keyword Analyzer:**
```bash
curl -X POST "localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "keyword",
  "text": "Product-SKU-12345"
}
'
# Output: ["Product-SKU-12345"] - no tokenization
```

### Custom Analyzers

Create analyzers tailored to your specific needs:

```bash
curl -X PUT "localhost:9200/articles" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "analysis": {
      "char_filter": {
        "html_strip_filter": {
          "type": "html_strip"
        }
      },
      "tokenizer": {
        "custom_tokenizer": {
          "type": "pattern",
          "pattern": "[\\W]+"
        }
      },
      "filter": {
        "custom_lowercase": {
          "type": "lowercase"
        },
        "custom_stop": {
          "type": "stop",
          "stopwords": ["the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        },
        "custom_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "custom_synonym": {
          "type": "synonym",
          "synonyms": [
            "quick,fast,rapid",
            "big,large,huge",
            "small,tiny,little"
          ]
        }
      },
      "analyzer": {
        "content_analyzer": {
          "type": "custom",
          "char_filter": ["html_strip_filter"],
          "tokenizer": "standard",
          "filter": [
            "custom_lowercase",
            "custom_stop",
            "custom_synonym",
            "custom_stemmer"
          ]
        },
        "search_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "custom_lowercase",
            "custom_stop",
            "custom_synonym"
          ]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "content_analyzer",
        "search_analyzer": "search_analyzer"
      },
      "content": {
        "type": "text",
        "analyzer": "content_analyzer",
        "search_analyzer": "search_analyzer"
      }
    }
  }
}
'
```

### Multi-language Analysis

```bash
curl -X PUT "localhost:9200/documents" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "fields": {
          "en": {"type": "text", "analyzer": "english"},
          "es": {"type": "text", "analyzer": "spanish"},
          "fr": {"type": "text", "analyzer": "french"},
          "de": {"type": "text", "analyzer": "german"}
        }
      },
      "content": {
        "type": "text",
        "fields": {
          "en": {"type": "text", "analyzer": "english"},
          "es": {"type": "text", "analyzer": "spanish"},
          "fr": {"type": "text", "analyzer": "french"},
          "de": {"type": "text", "analyzer": "german"}
        }
      }
    }
  }
}
'
```

## 🎯 Advanced Query Patterns

### Match Query Variations

**Basic Match with Options:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "content": {
        "query": "elasticsearch performance optimization",
        "operator": "and",
        "minimum_should_match": "75%",
        "fuzziness": "AUTO",
        "prefix_length": 2,
        "max_expansions": 10
      }
    }
  }
}
'
```

**Match Phrase with Slop:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_phrase": {
      "content": {
        "query": "machine learning algorithms",
        "slop": 2  // Allow up to 2 words between terms
      }
    }
  }
}
'
```

**Match Phrase Prefix for Autocomplete:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_phrase_prefix": {
      "title": {
        "query": "elasticsearch tuto",
        "max_expansions": 10,
        "slop": 1
      }
    }
  }
}
'
```

### Multi-field Search

**Cross-field Search:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "type": "cross_fields",
      "fields": ["title^3", "content", "tags^2"],
      "operator": "and"
    }
  }
}
'
```

**Best Fields with Tie Breaker:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "machine learning",
      "type": "best_fields",
      "fields": ["title^2", "content", "summary"],
      "tie_breaker": 0.3,
      "minimum_should_match": "50%"
    }
  }
}
'
```

**Most Fields for Comprehensive Matching:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "python programming",
      "type": "most_fields",
      "fields": [
        "title",
        "title.english",
        "content",
        "content.english",
        "tags"
      ]
    }
  }
}
'
```

### Boolean Query Combinations

**Complex Boolean Logic:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "elasticsearch",
            "fields": ["title^3", "content"]
          }
        }
      ],
      "should": [
        {"match": {"content": "performance"}},
        {"match": {"content": "optimization"}},
        {"match": {"content": "tuning"}},
        {"match": {"tags": "tutorial"}}
      ],
      "minimum_should_match": 1,
      "filter": [
        {"term": {"status": "published"}},
        {"range": {"publish_date": {"gte": "2023-01-01"}}}
      ],
      "must_not": [
        {"term": {"tags": "deprecated"}},
        {"match": {"content": "outdated"}}
      ]
    }
  }
}
'
```

**Boosting Strategy:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "boosting": {
      "positive": {
        "multi_match": {
          "query": "elasticsearch tutorial",
          "fields": ["title^2", "content"]
        }
      },
      "negative": {
        "multi_match": {
          "query": "deprecated old version",
          "fields": ["content", "tags"]
        }
      },
      "negative_boost": 0.2
    }
  }
}
'
```

## 🎚️ Relevance Tuning

### Field Boosting

```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch performance",
      "fields": [
        "title^5",           // Title is very important
        "summary^3",         // Summary is important
        "content^1",         // Content has base weight
        "tags^2",           // Tags are moderately important
        "author^0.5"        // Author is less important
      ]
    }
  }
}
'
```

### Function Score Queries

**Boost by Popularity:**
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
          "field_value_factor": {
            "field": "view_count",
            "factor": 0.1,
            "modifier": "log1p",
            "missing": 0
          }
        },
        {
          "field_value_factor": {
            "field": "like_count",
            "factor": 0.2,
            "modifier": "sqrt",
            "missing": 0
          }
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply",
      "max_boost": 2.0
    }
  }
}
'
```

**Time Decay Function:**
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

**Custom Script Scoring:**
```bash
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "match": {"title": "elasticsearch"}
      },
      "script_score": {
        "script": {
          "source": "Math.log(2 + doc['\''view_count'\''].value) * params.factor",
          "params": {
            "factor": 1.2
          }
        }
      }
    }
  }
}
'
```

## 🌍 Language-specific Search

### Detecting Language

```bash
# Index with language detection
curl -X PUT "localhost:9200/multilingual" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "analysis": {
      "analyzer": {
        "multilingual_analyzer": {
          "type": "standard",
          "stopwords": "_none_"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "multilingual_analyzer",
        "fields": {
          "english": {"type": "text", "analyzer": "english"},
          "spanish": {"type": "text", "analyzer": "spanish"},
          "french": {"type": "text", "analyzer": "french"}
        }
      },
      "language": {"type": "keyword"}
    }
  }
}
'
```

### Language-specific Queries

```bash
# Search with language detection
curl -X POST "localhost:9200/multilingual/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {
          "bool": {
            "must": [
              {"term": {"language": "en"}},
              {"match": {"content.english": "machine learning"}}
            ]
          }
        },
        {
          "bool": {
            "must": [
              {"term": {"language": "es"}},
              {"match": {"content.spanish": "aprendizaje automático"}}
            ]
          }
        },
        {
          "bool": {
            "must": [
              {"term": {"language": "fr"}},
              {"match": {"content.french": "apprentissage automatique"}}
            ]
          }
        }
      ]
    }
  }
}
'
```

## ⌨️ Search-as-you-type

### Completion Suggester

```bash
# Setup completion suggester
curl -X PUT "localhost:9200/autocomplete" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "suggest": {
        "type": "completion",
        "analyzer": "simple",
        "preserve_separators": true,
        "preserve_position_increments": true,
        "max_input_length": 50,
        "contexts": [
          {
            "name": "category",
            "type": "category"
          }
        ]
      }
    }
  }
}
'

# Index documents with suggestions
curl -X POST "localhost:9200/autocomplete/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Elasticsearch Tutorial for Beginners",
  "suggest": {
    "input": ["elasticsearch", "tutorial", "beginners", "elasticsearch tutorial"],
    "contexts": {
      "category": ["technology", "programming"]
    }
  }
}
'

# Search suggestions
curl -X POST "localhost:9200/autocomplete/_search" -H 'Content-Type: application/json' -d'
{
  "suggest": {
    "title_suggest": {
      "prefix": "elast",
      "completion": {
        "field": "suggest",
        "size": 5,
        "contexts": {
          "category": ["technology"]
        }
      }
    }
  }
}
'
```

### Edge N-gram for Prefix Matching

```bash
curl -X PUT "localhost:9200/search_suggestions" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "analysis": {
      "tokenizer": {
        "edge_ngram_tokenizer": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20,
          "token_chars": ["letter", "digit"]
        }
      },
      "analyzer": {
        "edge_ngram_analyzer": {
          "type": "custom",
          "tokenizer": "edge_ngram_tokenizer",
          "filter": ["lowercase"]
        },
        "search_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "edge_ngram_analyzer",
        "search_analyzer": "search_analyzer"
      }
    }
  }
}
'
```

## 🔤 Fuzzy and Phonetic Search

### Fuzzy Search

```bash
# Automatic fuzziness
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": {
        "query": "elasticsearh",  // Typo
        "fuzziness": "AUTO",
        "prefix_length": 2,
        "max_expansions": 10
      }
    }
  }
}
'

# Manual fuzziness
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {
      "title": {
        "value": "elasticsearh",
        "fuzziness": 2,
        "prefix_length": 2,
        "max_expansions": 50
      }
    }
  }
}
'
```

### Phonetic Search

```bash
curl -X PUT "localhost:9200/phonetic_search" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "analysis": {
      "filter": {
        "metaphone_filter": {
          "type": "phonetic",
          "encoder": "metaphone",
          "replace": false
        },
        "soundex_filter": {
          "type": "phonetic",
          "encoder": "soundex",
          "replace": false
        }
      },
      "analyzer": {
        "phonetic_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "metaphone_filter"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "fields": {
          "phonetic": {
            "type": "text",
            "analyzer": "phonetic_analyzer"
          }
        }
      }
    }
  }
}
'

# Search phonetically similar names
curl -X POST "localhost:9200/phonetic_search/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "john",
      "fields": ["name", "name.phonetic"],
      "type": "most_fields"
    }
  }
}
'
```

## 🚀 Performance Optimization

### Index Time Optimization

```bash
# Optimized mapping for search performance
curl -X PUT "localhost:9200/optimized_articles" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "30s",
    "analysis": {
      "analyzer": {
        "fast_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "fast_analyzer",
        "norms": false,  // Disable if length normalization not needed
        "index_options": "freqs"  // Store term frequencies only
      },
      "content": {
        "type": "text",
        "analyzer": "fast_analyzer"
      },
      "category": {
        "type": "keyword",
        "doc_values": true  // Enable for aggregations
      },
      "metadata": {
        "type": "object",
        "enabled": false  // Don'\''t index metadata
      }
    }
  }
}
'
```

### Query Time Optimization

```bash
# Use constant score for filter-only queries
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "constant_score": {
      "filter": {
        "bool": {
          "must": [
            {"term": {"status": "published"}},
            {"range": {"publish_date": {"gte": "2024-01-01"}}}
          ]
        }
      },
      "boost": 1.0
    }
  }
}
'

# Limit analyzed text length
curl -X POST "localhost:9200/articles/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "content": {
        "query": "elasticsearch performance",
        "max_analyzed_offset": 1000000
      }
    }
  }
}
'
```

## 🎯 Real-world Examples

### E-commerce Product Search

```bash
# Comprehensive product search
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "function_score": {
      "query": {
        "bool": {
          "must": [
            {
              "multi_match": {
                "query": "wireless bluetooth headphones",
                "fields": [
                  "name^3",
                  "description^1.5",
                  "brand^2",
                  "features",
                  "category"
                ],
                "type": "best_fields",
                "tie_breaker": 0.3,
                "fuzziness": "AUTO"
              }
            }
          ],
          "should": [
            {"match": {"name": {"query": "premium", "boost": 1.5}}},
            {"match": {"features": {"query": "noise canceling", "boost": 2.0}}}
          ],
          "filter": [
            {"term": {"in_stock": true}},
            {"range": {"price": {"gte": 50, "lte": 500}}},
            {"term": {"condition": "new"}}
          ]
        }
      },
      "functions": [
        {
          "field_value_factor": {
            "field": "rating",
            "factor": 0.1,
            "modifier": "log1p"
          }
        },
        {
          "field_value_factor": {
            "field": "sales_count",
            "factor": 0.05,
            "modifier": "sqrt"
          }
        },
        {
          "exp": {
            "created_date": {
              "origin": "now",
              "scale": "90d",
              "decay": 0.5
            }
          }
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply"
    }
  },
  "highlight": {
    "fields": {
      "name": {"number_of_fragments": 0},
      "description": {"fragment_size": 150}
    }
  },
  "size": 20
}
'
```

### Document Search with Relevance

```bash
# Academic paper search
curl -X POST "localhost:9200/papers/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "machine learning neural networks",
            "fields": ["title^4", "abstract^2", "keywords^3"],
            "type": "best_fields",
            "tie_breaker": 0.2
          }
        },
        {
          "match_phrase": {
            "abstract": {
              "query": "deep learning",
              "boost": 2.0
            }
          }
        }
      ],
      "filter": [
        {"range": {"publication_year": {"gte": 2020}}},
        {"term": {"peer_reviewed": true}}
      ]
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"citation_count": {"order": "desc"}}
  ]
}
'
```

## 🔗 Next Steps

Now that you've mastered full-text search, let's explore data analysis capabilities:

1. **[Aggregations](aggregations.md)** - Analyze and summarize your search results
2. **[Relevance Scoring](relevance-scoring.md)** - Fine-tune search result ranking
3. **[Vector Search](../05-modern-capabilities/vector-search.md)** - Modern semantic search capabilities

## 📚 Key Takeaways

- ✅ **Choose appropriate analyzers** for your content and language
- ✅ **Use multi-field mappings** for different search patterns
- ✅ **Implement proper boosting strategies** for relevance
- ✅ **Optimize for search-as-you-type** with completion suggesters
- ✅ **Handle typos and variations** with fuzzy search
- ✅ **Consider performance implications** of complex analysis
- ✅ **Test with real user queries** to validate search quality
- ✅ **Monitor search performance** and adjust accordingly

Ready to analyze your search data? Continue with [Aggregations](aggregations.md) to learn powerful analytics capabilities!