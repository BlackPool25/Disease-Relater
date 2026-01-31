-- Migration: 001_add_composite_index
-- Description: Add composite index on (disease_1_id, disease_2_id) for efficient relationship lookups
-- Date: 2026-01-30
-- Author: Agent 2 (Database Optimization)

-- Create composite index for relationship lookups
-- This index significantly improves query performance when looking up relationships
-- between specific disease pairs, as it allows PostgreSQL to use a single index scan
-- instead of combining results from two separate index scans.
CREATE INDEX IF NOT EXISTS idx_rel_composite 
ON disease_relationships(disease_1_id, disease_2_id);

-- Update table statistics for the query planner
-- This helps PostgreSQL make better decisions about query execution plans
ANALYZE disease_relationships;

-- Verify the index was created (for manual verification)
-- Run this query to check:
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'disease_relationships';
