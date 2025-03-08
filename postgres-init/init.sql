-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Install Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Set Apache AGE search path
SET search_path = ag_catalog, public;

-- Create AGE graph
SELECT create_graph('chunk_entity_relation');
