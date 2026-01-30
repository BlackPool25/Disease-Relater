#!/bin/bash
# Execute all disease import batches via Supabase MCP

PROJECT_ID="gbohehihcncmlcpyxomv"
BATCH_DIR="/tmp"

echo "Starting disease import to Supabase..."
echo "Project ID: $PROJECT_ID"
echo ""

# Execute each batch
for batch_file in $BATCH_DIR/diseases_batch_*.sql; do
    batch_name=$(basename "$batch_file")
    echo "Executing $batch_name..."
    
    # Read SQL and execute via MCP
    sql=$(cat "$batch_file")
    
    # Use supabase-mcp-server_execute_sql
    # Note: This is a placeholder - actual execution requires interactive MCP tool usage
    echo "  ✓ Batch ready for execution"
done

echo ""
echo "All 13 batches prepared for import"
echo "Execute using: supabase-mcp-server_execute_sql with each batch SQL"
