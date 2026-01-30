"""
Database Query Functions Module

Agent 3: Query Functions and API Layer
This module provides Python functions for querying the Disease-Relater database.
All queries are parameterized for security and performance.

Author: Agent 3
Date: 2026-01-30

Functions:
    get_disease_by_code: Query disease by ICD code
    get_diseases_by_chapter: Query diseases by chapter
    get_related_diseases: Get related diseases ordered by odds ratio
    get_network_data: Get all nodes and edges for visualization
    get_prevalence_for_demographics: Get prevalence by sex and age
"""

import logging
from typing import Dict, List, Optional, Any, Union
import os

logger = logging.getLogger(__name__)


class DatabaseQueries:
    """
    Database query class for Disease-Relater.

    Provides methods to query diseases, relationships, and network data.
    Designed to work with Supabase PostgreSQL database.
    """

    def __init__(self, supabase_client=None):
        """
        Initialize with optional Supabase client.

        Args:
            supabase_client: Initialized Supabase client instance
        """
        self.client = supabase_client
        self.logger = logging.getLogger(__name__)

    def _execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute SQL query and return results.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of result dictionaries

        Note:
            If supabase_client is not provided, returns empty list.
            In production, this would execute via Supabase RPC or REST API.
        """
        if self.client is None:
            self.logger.warning("No Supabase client configured")
            return []

        try:
            result = self.client.rpc(
                "exec_sql", {"query": query, "params": params}
            ).execute()
            return result.data if result.data else []
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            return []

    def get_disease_by_code(self, icd_code: str) -> Optional[Dict[str, Any]]:
        """
        Query 1: Get disease by ICD code.

        Returns complete disease record with chapter info and 3D coordinates.

        Args:
            icd_code: ICD-10 code (e.g., 'E11', 'I10')

        Returns:
            Disease record dictionary or None if not found

        Example:
            >>> db = DatabaseQueries(client)
            >>> disease = db.get_disease_by_code('E11')
            >>> print(disease['name_english'])
            'Type 2 diabetes mellitus'

        SQL Reference:
            See database/queries.sql - QUERY 1
        """
        if not icd_code or not isinstance(icd_code, str):
            self.logger.error("Invalid icd_code parameter")
            return None

        query = """
            SELECT
                d.id,
                d.icd_code,
                d.name_english,
                d.name_german,
                d.chapter_code,
                c.chapter_name,
                d.granularity,
                d.prevalence_male,
                d.prevalence_female,
                d.prevalence_total,
                d.vector_x,
                d.vector_y,
                d.vector_z,
                d.has_english_name,
                d.has_3d_coordinates,
                d.created_at,
                d.updated_at
            FROM diseases d
            LEFT JOIN icd_chapters c ON d.chapter_code = c.chapter_code
            WHERE d.icd_code = %(icd_code)s
        """

        results = self._execute_query(query, {"icd_code": icd_code})

        if results:
            return results[0]

        self.logger.info(f"Disease not found: {icd_code}")
        return None

    def get_diseases_by_chapter(
        self,
        chapter_code: str,
        limit: int = 100,
        offset: int = 0,
        min_prevalence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query 2: Get all diseases in a chapter.

        Returns paginated list of diseases in a specific ICD chapter.

        Args:
            chapter_code: ICD chapter code (e.g., 'I', 'IX', 'X')
            limit: Maximum number of results (default: 100)
            offset: Pagination offset (default: 0)
            min_prevalence: Filter by minimum prevalence (optional)

        Returns:
            List of disease records

        Example:
            >>> db = DatabaseQueries(client)
            >>> diseases = db.get_diseases_by_chapter('IX', limit=20)
            >>> print(f"Found {len(diseases)} circulatory diseases")

        SQL Reference:
            See database/queries.sql - QUERY 2
        """
        if not chapter_code or not isinstance(chapter_code, str):
            self.logger.error("Invalid chapter_code parameter")
            return []

        params = {
            "chapter_code": chapter_code,
            "limit": min(limit, 1000),
            "offset": max(offset, 0),
        }

        query = """
            SELECT 
                d.id,
                d.icd_code,
                d.name_english,
                d.name_german,
                d.chapter_code,
                c.chapter_name,
                d.granularity,
                d.prevalence_total,
                d.has_english_name,
                d.has_3d_coordinates
            FROM diseases d
            LEFT JOIN icd_chapters c ON d.chapter_code = c.chapter_code
            WHERE d.chapter_code = %(chapter_code)s
        """

        if min_prevalence is not None:
            query += " AND d.prevalence_total >= %(min_prevalence)s"
            params["min_prevalence"] = min_prevalence

        query += """
            ORDER BY d.icd_code
            LIMIT %(limit)s OFFSET %(offset)s
        """

        return self._execute_query(query, params)

    def get_related_diseases(
        self,
        icd_code: str,
        limit: int = 50,
        min_odds_ratio: float = 1.5,
        bidirectional: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Query 3: Get related diseases ordered by odds ratio.

        Returns diseases with highest comorbidity (highest odds ratio).

        Args:
            icd_code: ICD-10 code to find relationships for
            limit: Maximum number of results (default: 50)
            min_odds_ratio: Minimum odds ratio threshold (default: 1.5)
            bidirectional: Search both directions (default: True)

        Returns:
            List of related diseases with relationship metrics

        Example:
            >>> db = DatabaseQueries(client)
            >>> related = db.get_related_diseases('E11', limit=10)
            >>> for r in related:
            ...     print(f"{r['icd_code']}: OR={r['odds_ratio']:.2f}")

        SQL Reference:
            See database/queries.sql - QUERY 3
        """
        if not icd_code or not isinstance(icd_code, str):
            self.logger.error("Invalid icd_code parameter")
            return []

        params = {
            "icd_code": icd_code,
            "limit": min(limit, 1000),
            "min_odds_ratio": min_odds_ratio,
        }

        if bidirectional:
            query = """
                SELECT 
                    related.id,
                    related.icd_code,
                    related.name_english,
                    related.name_german,
                    related.chapter_code,
                    dr.odds_ratio,
                    dr.p_value,
                    dr.patient_count_total,
                    dr.relationship_strength
                FROM disease_relationships dr
                JOIN diseases current ON (dr.disease_1_id = current.id OR dr.disease_2_id = current.id)
                JOIN diseases related ON (
                    (dr.disease_1_id = current.id AND dr.disease_2_id = related.id) OR
                    (dr.disease_2_id = current.id AND dr.disease_1_id = related.id)
                )
                WHERE current.icd_code = %(icd_code)s
                  AND related.id != current.id
                  AND dr.odds_ratio >= %(min_odds_ratio)s
                ORDER BY dr.odds_ratio DESC
                LIMIT %(limit)s
            """
        else:
            query = """
                SELECT 
                    d2.id,
                    d2.icd_code,
                    d2.name_english,
                    d2.name_german,
                    d2.chapter_code,
                    dr.odds_ratio,
                    dr.p_value,
                    dr.patient_count_total,
                    dr.relationship_strength
                FROM disease_relationships dr
                JOIN diseases d1 ON dr.disease_1_id = d1.id
                JOIN diseases d2 ON dr.disease_2_id = d2.id
                WHERE d1.icd_code = %(icd_code)s
                  AND dr.odds_ratio >= %(min_odds_ratio)s
                ORDER BY dr.odds_ratio DESC
                LIMIT %(limit)s
            """

        return self._execute_query(query, params)

    def get_network_data(
        self,
        min_odds_ratio: float = 2.0,
        max_edges: Optional[int] = None,
        chapter_filter: Optional[str] = None,
    ) -> Dict[str, List[Dict]]:
        """
        Query 4: Get all nodes and edges for network visualization.

        Returns complete network data structured for visualization.

        Args:
            min_odds_ratio: Minimum odds ratio for edges (default: 2.0)
            max_edges: Maximum number of edges to return (optional)
            chapter_filter: Filter nodes by chapter code (optional)

        Returns:
            Dictionary with 'nodes' and 'edges' lists

        Example:
            >>> db = DatabaseQueries(client)
            >>> network = db.get_network_data(min_odds_ratio=5.0)
            >>> print(f"Nodes: {len(network['nodes'])}, Edges: {len(network['edges'])}")

        SQL Reference:
            See database/queries.sql - QUERY 4
        """
        nodes_query = """
            SELECT 
                id,
                icd_code,
                name_english,
                name_german,
                chapter_code,
                vector_x,
                vector_y,
                vector_z,
                prevalence_total
            FROM diseases
            WHERE has_3d_coordinates = true
        """

        nodes_params = {}
        if chapter_filter:
            nodes_query += " AND chapter_code = %(chapter_filter)s"
            nodes_params["chapter_filter"] = chapter_filter

        nodes_query += " ORDER BY chapter_code, icd_code"

        edges_query = """
            SELECT 
                dr.disease_1_id,
                d1.icd_code as disease_1_code,
                d1.name_english as disease_1_name,
                dr.disease_2_id,
                d2.icd_code as disease_2_code,
                d2.name_english as disease_2_name,
                dr.odds_ratio,
                dr.p_value,
                dr.relationship_strength,
                dr.patient_count_total
            FROM disease_relationships dr
            JOIN diseases d1 ON dr.disease_1_id = d1.id
            JOIN diseases d2 ON dr.disease_2_id = d2.id
            WHERE dr.odds_ratio >= %(min_odds_ratio)s
        """

        edges_params = {"min_odds_ratio": min_odds_ratio}

        if chapter_filter:
            edges_query += """
                AND (d1.chapter_code = %(chapter_filter)s OR d2.chapter_code = %(chapter_filter)s)
            """
            edges_params["chapter_filter"] = chapter_filter

        edges_query += " ORDER BY dr.odds_ratio DESC"

        if max_edges:
            edges_query += " LIMIT %(max_edges)s"
            edges_params["max_edges"] = max_edges

        nodes = self._execute_query(nodes_query, nodes_params)
        edges = self._execute_query(edges_query, edges_params)

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "min_odds_ratio": min_odds_ratio,
                "chapter_filter": chapter_filter,
                "total_nodes": len(nodes),
                "total_edges": len(edges),
            },
        }

    def get_prevalence_for_demographics(
        self, icd_code: str, sex: str = "All", age_group: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query 5: Get prevalence for specific demographics.

        Returns prevalence data for a disease filtered by sex and age.

        Args:
            icd_code: ICD-10 code
            sex: Sex filter ('Male', 'Female', 'All') - default: 'All'
            age_group: Age group filter (optional, e.g., '70-79')

        Returns:
            Dictionary with prevalence data or None

        Example:
            >>> db = DatabaseQueries(client)
            >>> prev = db.get_prevalence_for_demographics('E11', sex='Female')
            >>> print(f"Prevalence: {prev['prevalence']:.4f}")

        SQL Reference:
            See database/queries.sql - QUERY 5
        """
        if not icd_code or not isinstance(icd_code, str):
            self.logger.error("Invalid icd_code parameter")
            return None

        # Validate sex parameter
        if sex not in ["Male", "Female", "All"]:
            self.logger.error(f"Invalid sex parameter: {sex}")
            return None

        # Query from diseases table (pre-aggregated)
        query = """
            SELECT 
                d.icd_code,
                d.name_english,
                d.name_german,
                d.chapter_code,
                CASE 
                    WHEN %(sex)s = 'Male' THEN d.prevalence_male
                    WHEN %(sex)s = 'Female' THEN d.prevalence_female
                    ELSE d.prevalence_total
                END as prevalence,
                d.prevalence_male,
                d.prevalence_female,
                d.prevalence_total
            FROM diseases d
            WHERE d.icd_code = %(icd_code)s
        """

        params = {"icd_code": icd_code, "sex": sex}

        results = self._execute_query(query, params)

        if not results:
            return None

        result = results[0]

        # If age_group specified, query stratified data for more detail
        if age_group and sex != "All":
            stratified_query = """
                SELECT 
                    drs.age_group,
                    AVG(drs.patient_count) as avg_patient_count,
                    COUNT(*) as relationship_count,
                    AVG(drs.odds_ratio) as avg_odds_ratio
                FROM disease_relationships_stratified drs
                JOIN diseases d ON drs.disease_1_id = d.id
                WHERE d.icd_code = %(icd_code)s
                  AND drs.sex = %(sex)s
                  AND drs.age_group = %(age_group)s
                GROUP BY drs.age_group
            """

            stratified_params = {
                "icd_code": icd_code,
                "sex": sex,
                "age_group": age_group,
            }

            stratified_results = self._execute_query(
                stratified_query, stratified_params
            )

            if stratified_results:
                result["stratified"] = stratified_results[0]

        return result

    def search_diseases(
        self,
        search_term: str,
        limit: int = 20,
        search_in_names: bool = True,
        search_in_codes: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Utility: Search diseases by name or code.

        Full-text search across disease names and codes.
        Uses parameterized queries to prevent SQL injection.

        Args:
            search_term: Search string
            limit: Maximum results (default: 20)
            search_in_names: Search in name fields (default: True)
            search_in_codes: Search in ICD codes (default: True)

        Returns:
            List of matching disease records
        """
        # Validate inputs
        if not search_term or len(search_term.strip()) < 2:
            return []

        # Sanitize and validate limit
        try:
            limit_val = min(int(limit), 100)
            if limit_val < 1:
                limit_val = 20
        except (ValueError, TypeError):
            limit_val = 20

        # Build query dynamically but safely (conditions are hardcoded, not user input)
        params: Dict[str, Any] = {
            "search_term": f"%{search_term.strip()}%",
            "limit": limit_val,
        }

        # Build WHERE clause based on search options
        where_clauses = []
        if search_in_names:
            where_clauses.append(
                "(d.name_english ILIKE %(search_term)s OR d.name_german ILIKE %(search_term)s)"
            )
        if search_in_codes:
            where_clauses.append("d.icd_code ILIKE %(search_term)s")

        if not where_clauses:
            return []

        # Use safe string joining for WHERE clause (no user input in conditions)
        where_clause = " OR ".join(where_clauses)

        query = f"""
            SELECT
                d.id,
                d.icd_code,
                d.name_english,
                d.name_german,
                d.chapter_code,
                c.chapter_name,
                d.prevalence_total,
                d.has_english_name
            FROM diseases d
            LEFT JOIN icd_chapters c ON d.chapter_code = c.chapter_code
            WHERE {where_clause}
            ORDER BY d.icd_code
            LIMIT %(limit)s
        """

        return self._execute_query(query, params)

    def get_disease_statistics(self) -> Dict[str, Any]:
        """
        Utility: Get overall database statistics.

        Returns summary statistics about diseases and relationships.

        Returns:
            Dictionary with statistics
        """
        diseases_query = """
            SELECT 
                COUNT(*) as total_diseases,
                COUNT(CASE WHEN has_english_name THEN 1 END) as with_english_names,
                COUNT(CASE WHEN has_3d_coordinates THEN 1 END) as with_3d_coords,
                COUNT(CASE WHEN has_prevalence_data THEN 1 END) as with_prevalence,
                AVG(prevalence_total) as avg_prevalence,
                COUNT(DISTINCT chapter_code) as chapters_count
            FROM diseases
        """

        relationships_query = """
            SELECT 
                relationship_strength,
                COUNT(*) as count,
                AVG(odds_ratio) as avg_odds_ratio
            FROM disease_relationships
            GROUP BY relationship_strength
            ORDER BY avg_odds_ratio DESC
        """

        diseases_stats = self._execute_query(diseases_query)
        relationships_stats = self._execute_query(relationships_query)

        return {
            "diseases": diseases_stats[0] if diseases_stats else {},
            "relationships_by_strength": relationships_stats,
            "database_status": "active" if self.client else "disconnected",
        }

    def get_chapter_statistics(self) -> List[Dict[str, Any]]:
        """
        Utility: Get statistics by ICD chapter.

        Returns disease counts and prevalence by chapter.

        Returns:
            List of chapter statistics
        """
        query = """
            SELECT 
                c.chapter_code,
                c.chapter_name,
                COUNT(d.id) as disease_count,
                AVG(d.prevalence_total) as avg_prevalence,
                COUNT(CASE WHEN d.has_3d_coordinates THEN 1 END) as with_3d
            FROM icd_chapters c
            LEFT JOIN diseases d ON c.chapter_code = d.chapter_code
            GROUP BY c.chapter_code, c.chapter_name
            ORDER BY disease_count DESC
        """

        return self._execute_query(query)


# Convenience functions for direct use (without class instantiation)


def get_disease_by_code(icd_code: str, client=None) -> Optional[Dict[str, Any]]:
    """Standalone function wrapper for get_disease_by_code."""
    db = DatabaseQueries(client)
    return db.get_disease_by_code(icd_code)


def get_diseases_by_chapter(
    chapter_code: str, limit: int = 100, client=None
) -> List[Dict[str, Any]]:
    """Standalone function wrapper for get_diseases_by_chapter."""
    db = DatabaseQueries(client)
    return db.get_diseases_by_chapter(chapter_code, limit)


def get_related_diseases(
    icd_code: str, limit: int = 50, client=None
) -> List[Dict[str, Any]]:
    """Standalone function wrapper for get_related_diseases."""
    db = DatabaseQueries(client)
    return db.get_related_diseases(icd_code, limit)


def get_network_data(min_odds_ratio: float = 2.0, client=None) -> Dict[str, List[Dict]]:
    """Standalone function wrapper for get_network_data."""
    db = DatabaseQueries(client)
    return db.get_network_data(min_odds_ratio)


def get_prevalence_for_demographics(
    icd_code: str, sex: str = "All", age_group: Optional[str] = None, client=None
) -> Optional[Dict[str, Any]]:
    """Standalone function wrapper for get_prevalence_for_demographics."""
    db = DatabaseQueries(client)
    return db.get_prevalence_for_demographics(icd_code, sex, age_group)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example: Show SQL queries without executing
    print("=" * 60)
    print("Disease-Relater Database Query Functions")
    print("=" * 60)
    print("\nThis module provides 5 core query functions:\n")

    print("1. get_disease_by_code(icd_code)")
    print("   - Query disease by ICD-10 code")
    print("   - Returns: dict with disease metadata\n")

    print("2. get_diseases_by_chapter(chapter_code, limit)")
    print("   - Get all diseases in an ICD chapter")
    print("   - Returns: list of disease records\n")

    print("3. get_related_diseases(icd_code, limit)")
    print("   - Get diseases with highest comorbidity")
    print("   - Returns: list ordered by odds ratio\n")

    print("4. get_network_data(min_odds_ratio)")
    print("   - Get nodes and edges for visualization")
    print("   - Returns: dict with 'nodes' and 'edges' lists\n")

    print("5. get_prevalence_for_demographics(icd_code, sex, age_group)")
    print("   - Get prevalence for specific demographics")
    print("   - Returns: dict with prevalence data\n")

    print("=" * 60)
    print("Usage Example:")
    print("=" * 60)
    print("""
from supabase import create_client
from scripts.db_queries import DatabaseQueries

# Initialize Supabase client
supabase = create_client(url, key)

# Create query instance
db = DatabaseQueries(supabase)

# Query disease by code
disease = db.get_disease_by_code('E11')
print(disease['name_english'])  # Type 2 diabetes mellitus

# Get related diseases
related = db.get_related_diseases('E11', limit=10)
for r in related:
    print(f"{r['icd_code']}: OR={r['odds_ratio']:.2f}")
    """)
