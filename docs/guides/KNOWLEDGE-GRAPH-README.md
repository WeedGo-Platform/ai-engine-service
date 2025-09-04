# Cannabis Knowledge Graph System

A comprehensive knowledge graph system for cannabis products, strains, and effects, built with Neo4j, Elasticsearch, and advanced NLP capabilities.

## Features

### 1. Knowledge Graph (Neo4j)
- **Entity Types**: Strains, Products, Brands, Terpenes, Cannabinoids, Effects, Conditions
- **Relationships**: CONTAINS, TREATS, CAUSES, PARENT_OF, SIMILAR_TO, etc.
- **Graph Algorithms**: PageRank, community detection, path finding
- **Cypher Query Support**: Custom graph queries for complex relationships

### 2. Semantic Search Engine
- **Multi-modal Embeddings**: Text and product feature embeddings
- **Hybrid Search**: Combines keyword, semantic, and graph traversal
- **Intent Classification**: Medical, recreational, strain lookup, effect-based
- **Query Expansion**: Synonym expansion and term enrichment
- **Faceted Search**: Dynamic filters and aggregations

### 3. Cannabis Ontology
- **Comprehensive Taxonomy**: Complete cannabis domain knowledge
- **Terpene Profiles**: Effects, aromas, medical benefits
- **Medical Conditions**: Recommended cannabinoids and terpenes
- **Consumption Methods**: Onset, duration, bioavailability
- **Quality Indicators**: Visual, aroma, and lab testing criteria

### 4. Graph Analytics
- **Product Importance**: PageRank, betweenness, closeness centrality
- **Community Detection**: Strain families and product clusters
- **Recommendation Algorithms**: Graph-based, content-based, collaborative, hybrid
- **Market Analysis**: Trends, correlations, distribution analysis
- **Inventory Optimization**: Data-driven stock recommendations

### 5. Data Pipeline
- **ETL Processing**: Excel, CSV, JSON data sources
- **Entity Extraction**: NLP-based extraction from descriptions
- **Relationship Inference**: Automatic relationship discovery
- **Quality Validation**: Data integrity and completeness checks

## Installation

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- 8GB RAM minimum (16GB recommended)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Start Infrastructure Services
```bash
# Start Neo4j, Elasticsearch, Redis, and Postgres
docker-compose -f docker-compose-graph.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose-graph.yml ps

# Check Neo4j browser at http://localhost:7474
# Check Elasticsearch at http://localhost:9200
# Check Kibana at http://localhost:5601
```

### 3. Initialize Database
```bash
# Run migrations
python apply_migrations.py

# Build knowledge graph from data
python scripts/build_knowledge_graph.py --data-file data/datasets/OCS_Catalogue_31_Jul_2025_226PM.xlsx
```

## Usage

### Quick Test
```bash
# Run comprehensive test suite
python test_knowledge_graph.py
```

### Python API Examples

#### Initialize Services
```python
from services.knowledge_graph import KnowledgeGraphService
from services.semantic_search import SemanticSearchEngine
from services.graph_analytics import GraphAnalyticsService

# Initialize knowledge graph
graph_service = KnowledgeGraphService(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)
await graph_service.connect()

# Initialize search engine
search_engine = SemanticSearchEngine(
    es_host="localhost",
    es_port=9200,
    graph_service=graph_service
)
await search_engine.initialize()

# Initialize analytics
analytics = GraphAnalyticsService(graph_service)
```

#### Search Products
```python
# Semantic search
results = await search_engine.search(
    query="I need something for anxiety and sleep",
    limit=10
)

# Search with filters
results = await search_engine.search(
    query="high CBD",
    filters={
        'thc_max': 5,
        'cbd_min': 15,
        'category': ['tincture', 'capsule']
    }
)

# Get search facets
facets = await search_engine.get_facets()
```

#### Graph Queries
```python
# Find similar products
similar = await graph_service.find_similar_products(
    product_id="prod_001",
    limit=5
)

# Get product profile with all relationships
profile = await graph_service.get_product_profile("prod_001")

# Recommend products for medical condition
recommendations = await graph_service.recommend_products_for_condition(
    condition="anxiety",
    limit=10
)

# Custom Cypher query
query = """
MATCH (p:Product)-[:HAS_TERPENE]->(t:Terpene {name: 'limonene'})
WHERE p.thc_content > 15
RETURN p.id, p.name, p.thc_content
ORDER BY p.thc_content DESC
LIMIT 10
"""
results = await graph_service.execute_cypher(query)
```

#### Analytics and Recommendations
```python
# Calculate product importance
pagerank = await analytics.calculate_pagerank(EntityType.PRODUCT)

# Detect communities
communities = await analytics.detect_communities()

# Find strain families
families = await analytics.find_strain_families()

# Generate recommendations
user_preferences = {
    'liked_products': ['prod_001', 'prod_002'],
    'effects': ['relaxed', 'creative'],
    'terpenes': ['myrcene', 'limonene'],
    'thc_range': [15, 25]
}

recommendations = await analytics.recommend_products(
    user_preferences,
    strategy=RecommendationStrategy.HYBRID,
    limit=10
)

# Analyze market trends
trends = await analytics.analyze_market_trends()

# Optimize inventory
current_inventory = {'prod_001': 50, 'prod_002': 10}
optimization = await analytics.optimize_inventory(
    current_inventory,
    target_coverage=0.8
)
```

## API Endpoints

### REST API Integration
```python
# Add to api/main.py
from services.knowledge_graph import KnowledgeGraphService
from services.semantic_search import SemanticSearchEngine

@app.get("/api/graph/similar/{product_id}")
async def get_similar_products(product_id: str, limit: int = 10):
    similar = await graph_service.find_similar_products(product_id, limit)
    return {"products": similar}

@app.post("/api/search/semantic")
async def semantic_search(query: str, filters: dict = None):
    results = await search_engine.search(query, filters=filters)
    return {"results": results}

@app.get("/api/analytics/trends")
async def get_market_trends():
    trends = await analytics.analyze_market_trends()
    return trends
```

## Data Schema

### Product Entity
```json
{
  "id": "prod_001",
  "name": "Blue Dream Flower",
  "description": "Sativa-dominant hybrid",
  "category": "flower",
  "brand": "Premium Cannabis",
  "strain": "Blue Dream",
  "thc_content": 22.5,
  "cbd_content": 0.5,
  "price": 45.00,
  "terpenes": [
    {"name": "myrcene", "percentage": 0.8},
    {"name": "pinene", "percentage": 0.5}
  ],
  "effects": ["creative", "uplifted", "relaxed"],
  "flavors": ["berry", "sweet"],
  "aromas": ["blueberry", "earthy"]
}
```

### Graph Relationships
- `(Product)-[:DERIVED_FROM]->(Strain)`
- `(Product)-[:PRODUCED_BY]->(Brand)`
- `(Product)-[:HAS_TERPENE]->(Terpene)`
- `(Product)-[:HAS_EFFECT]->(Effect)`
- `(Effect)-[:TREATS]->(Condition)`
- `(Product)-[:SIMILAR_TO]->(Product)`

## Performance Optimization

### Caching
- Redis caching for frequent queries
- Graph analytics results cached for 1 hour
- Search results cached with query hash

### Indexing
- Neo4j: Unique constraints on IDs, indexes on categories
- Elasticsearch: Dense vector index for embeddings
- Full-text indexes on names and descriptions

### Batch Operations
- Bulk product indexing
- Batch graph updates
- Parallel search execution

## Monitoring

### Metrics
- Query performance tracking
- Cache hit rates
- Graph size and complexity
- Search relevance scores

### Health Checks
```bash
# Check service health
curl http://localhost:7474/db/neo4j/tx  # Neo4j
curl http://localhost:9200/_cluster/health  # Elasticsearch
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   ```bash
   # Check Neo4j is running
   docker ps | grep neo4j
   
   # View logs
   docker logs weedgo-neo4j
   ```

2. **Elasticsearch Index Error**
   ```bash
   # Delete and recreate index
   curl -X DELETE http://localhost:9200/cannabis_products
   python scripts/build_knowledge_graph.py
   ```

3. **Memory Issues**
   ```bash
   # Increase Docker memory
   docker-compose -f docker-compose-graph.yml down
   # Edit docker-compose-graph.yml memory limits
   docker-compose -f docker-compose-graph.yml up -d
   ```

## Development

### Running Tests
```bash
# Unit tests
pytest tests/unit/test_knowledge_graph.py

# Integration tests
pytest tests/integration/test_graph_integration.py

# Full demo
python test_knowledge_graph.py
```

### Adding New Entity Types
1. Update `EntityType` enum in `knowledge_graph.py`
2. Add constraints in `_create_constraints()`
3. Update ontology in `cannabis_ontology.json`
4. Extend pipeline in `build_knowledge_graph.py`

### Custom Analytics
```python
# Add to graph_analytics.py
async def custom_metric(self):
    query = """
    // Your custom Cypher query
    """
    results = await self.graph_service.execute_cypher(query)
    return process_results(results)
```

## Production Deployment

### Environment Variables
```bash
# .env.production
NEO4J_URI=bolt://production-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure_password
ELASTICSEARCH_HOST=production-es
ELASTICSEARCH_PORT=9200
REDIS_HOST=production-redis
```

### Scaling Considerations
- Neo4j Enterprise for clustering
- Elasticsearch cluster for high availability
- Redis Sentinel for failover
- Load balancing for API endpoints

### Backup Strategy
```bash
# Backup Neo4j
docker exec weedgo-neo4j neo4j-admin backup --to=/backups/

# Backup Elasticsearch
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
```

## License
Proprietary - WeedGo Inc.

## Support
For issues and questions, contact the AI Engine team.