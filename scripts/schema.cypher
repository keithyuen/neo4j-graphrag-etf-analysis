// ETF GraphRAG Schema Setup
// This file creates the complete Neo4j schema for the ETF GraphRAG system

// =============================================================================
// CONSTRAINTS AND INDEXES
// =============================================================================

// Core Business Entity Constraints
CREATE CONSTRAINT etf_ticker_unique IF NOT EXISTS FOR (e:ETF) REQUIRE e.ticker IS UNIQUE;
CREATE CONSTRAINT company_symbol_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.symbol IS UNIQUE;
CREATE CONSTRAINT sector_name_unique IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE;

// GraphRAG System Constraints
CREATE CONSTRAINT intent_key_unique IF NOT EXISTS FOR (i:Intent) REQUIRE i.key IS UNIQUE;
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT term_norm_unique IF NOT EXISTS FOR (t:Term) REQUIRE t.norm IS UNIQUE;
CREATE CONSTRAINT doc_chunk_id_unique IF NOT EXISTS FOR (d:DocChunk) REQUIRE d.id IS UNIQUE;

// =============================================================================
// PERFORMANCE INDEXES
// =============================================================================

// Business Logic Indexes
CREATE INDEX etf_name_index IF NOT EXISTS FOR (e:ETF) ON (e.name);
CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX company_industry_index IF NOT EXISTS FOR (c:Company) ON (c.industry);
CREATE INDEX sector_classification_index IF NOT EXISTS FOR (s:Sector) ON (s.classification);

// GraphRAG Performance Indexes
CREATE INDEX intent_type_index IF NOT EXISTS FOR (i:Intent) ON (i.type);
CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX entity_symbol_index IF NOT EXISTS FOR (e:Entity) ON (e.symbol);
CREATE INDEX term_text_index IF NOT EXISTS FOR (t:Term) ON (t.text);
CREATE INDEX doc_chunk_type_index IF NOT EXISTS FOR (d:DocChunk) ON (d.type);

// Relationship Indexes for Performance
CREATE INDEX holds_weight_index IF NOT EXISTS FOR ()-[r:HOLDS]-() ON (r.weight);
CREATE INDEX requires_param_index IF NOT EXISTS FOR ()-[r:REQUIRES]-() ON (r.param_name);
CREATE INDEX synonymous_confidence_index IF NOT EXISTS FOR ()-[r:SYNONYMOUS_WITH]-() ON (r.confidence);

// =============================================================================
// VECTOR INDEXES (Optional - for semantic search)
// =============================================================================

// Create vector index for DocChunk embeddings if using vector search
// This requires APOC and vector capabilities
// Uncomment if using embeddings:
// CALL db.index.vector.createNodeIndex(
//   'doc_chunk_embeddings',
//   'DocChunk',
//   'embedding',
//   1536,
//   'cosine'
// );

// =============================================================================
// SCHEMA VALIDATION RULES (Using APOC)
// =============================================================================

// Validate ETF ticker format (3-4 uppercase letters)
// CALL apoc.schema.assert(
//   {},
//   {ETF: ['UPPER(ticker) = ticker', 'SIZE(ticker) >= 3 AND SIZE(ticker) <= 4']}
// );

// Validate weight ranges (0 to 1)
// Note: This would be enforced at application level since Neo4j doesn't support
// relationship property constraints directly

// =============================================================================
// FULL-TEXT SEARCH INDEXES
// =============================================================================

// Full-text search for company names and ETF names
CREATE FULLTEXT INDEX company_search_index IF NOT EXISTS
FOR (c:Company) ON EACH [c.name, c.symbol];

CREATE FULLTEXT INDEX etf_search_index IF NOT EXISTS
FOR (e:ETF) ON EACH [e.name, e.ticker, e.description];

CREATE FULLTEXT INDEX sector_search_index IF NOT EXISTS
FOR (s:Sector) ON EACH [s.name, s.classification];

// Full-text search for GraphRAG terms and content
CREATE FULLTEXT INDEX term_search_index IF NOT EXISTS
FOR (t:Term) ON EACH [t.text, t.norm];

CREATE FULLTEXT INDEX doc_content_search_index IF NOT EXISTS
FOR (d:DocChunk) ON EACH [d.content, d.title];

// =============================================================================
// SCHEMA INFORMATION QUERIES
// =============================================================================

// Display all constraints
SHOW CONSTRAINTS;

// Display all indexes
SHOW INDEXES;

// Schema summary statistics
CALL apoc.meta.stats() YIELD labelCount, relTypeCount, propertyKeyCount, nodeCount, relCount
RETURN 
  labelCount as `Node Labels`,
  relTypeCount as `Relationship Types`, 
  propertyKeyCount as `Property Keys`,
  nodeCount as `Total Nodes`,
  relCount as `Total Relationships`;