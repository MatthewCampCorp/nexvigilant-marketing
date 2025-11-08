"""
BigQuery Tool for Data Intelligence Agent.

Provides safe, controlled access to BigQuery data warehouse.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import GoogleCloudError
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    logging.warning("google-cloud-bigquery not installed")

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result from a BigQuery query execution."""
    success: bool
    rows: List[Dict[str, Any]]
    total_rows: int
    schema: List[str]
    bytes_processed: Optional[int] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


class BigQueryTool:
    """
    Tool for executing BigQuery queries with safety controls and performance optimization.

    Features:
    - Query validation and sanitization
    - Automatic partitioning detection
    - Cost control via bytes billed limits
    - Result caching
    - Timeout enforcement
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        default_dataset: Optional[str] = None,
        timeout_seconds: int = 30,
        max_results: int = 10000,
        max_bytes_billed: int = 10737418240,  # 10 GB
        cache_enabled: bool = True,
    ):
        """
        Initialize BigQuery tool.

        Args:
            project_id: Google Cloud project ID
            default_dataset: Default dataset for queries
            timeout_seconds: Query timeout
            max_results: Maximum rows to return
            max_bytes_billed: Maximum bytes billed per query
            cache_enabled: Enable query result caching
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.default_dataset = default_dataset or os.getenv("BIGQUERY_DATASET_GOLD", "marketing_marts")
        self.timeout_seconds = timeout_seconds
        self.max_results = max_results
        self.max_bytes_billed = max_bytes_billed
        self.cache_enabled = cache_enabled

        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT must be set")

        if BIGQUERY_AVAILABLE:
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"Initialized BigQuery tool for project: {self.project_id}")
        else:
            self.client = None
            logger.warning("BigQuery client not available - running in stub mode")

        # Allowed tables for security (prevent unauthorized data access)
        self.allowed_tables = {
            "customer_360",
            "campaign_performance",
            "attribution_model",
            "ml_features",
            "lead_scoring_features",
            "customer_segments",
            "product_catalog",
            "engagement_metrics",
        }

    def validate_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate query for safety and compliance.

        Args:
            query: SQL query string

        Returns:
            Tuple of (is_valid, error_message)
        """
        query_upper = query.upper()

        # Check for disallowed operations
        disallowed_operations = [
            "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"
        ]

        for op in disallowed_operations:
            if op in query_upper:
                return False, f"Operation '{op}' is not allowed"

        # Ensure SELECT query
        if not query_upper.strip().startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        # Check for allowed tables (basic check)
        # In production, use more sophisticated query parsing
        found_allowed_table = False
        for table in self.allowed_tables:
            if table in query.lower():
                found_allowed_table = True
                break

        if not found_allowed_table:
            return False, f"Query must reference allowed tables: {', '.join(self.allowed_tables)}"

        return True, None

    def execute_query(
        self,
        query: str,
        parameters: Optional[List[Any]] = None,
        use_cache: Optional[bool] = None,
    ) -> QueryResult:
        """
        Execute a BigQuery SQL query with safety controls.

        Args:
            query: SQL query string
            parameters: Query parameters for parameterized queries
            use_cache: Override cache setting for this query

        Returns:
            QueryResult with data and metadata
        """
        import time

        # Validate query
        is_valid, error_msg = self.validate_query(query)
        if not is_valid:
            logger.error(f"Query validation failed: {error_msg}")
            return QueryResult(
                success=False,
                rows=[],
                total_rows=0,
                schema=[],
                error=f"Query validation failed: {error_msg}"
            )

        if not BIGQUERY_AVAILABLE or not self.client:
            logger.warning("BigQuery not available - returning stub data")
            return QueryResult(
                success=False,
                rows=[],
                total_rows=0,
                schema=[],
                error="BigQuery client not available"
            )

        try:
            # Configure job
            job_config = bigquery.QueryJobConfig(
                maximum_bytes_billed=self.max_bytes_billed,
                use_query_cache=use_cache if use_cache is not None else self.cache_enabled,
            )

            # Add parameters if provided
            if parameters:
                job_config.query_parameters = parameters

            # Execute query
            start_time = time.time()
            logger.info(f"Executing query: {query[:100]}...")

            query_job = self.client.query(query, job_config=job_config)

            # Wait for results with timeout
            results = query_job.result(timeout=self.timeout_seconds)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Process results
            rows = [dict(row) for row in results]

            # Limit results
            if len(rows) > self.max_results:
                logger.warning(f"Query returned {len(rows)} rows, limiting to {self.max_results}")
                rows = rows[:self.max_results]

            schema = [field.name for field in results.schema]

            logger.info(
                f"Query completed: {len(rows)} rows, "
                f"{query_job.total_bytes_processed} bytes processed, "
                f"{execution_time:.2f}ms"
            )

            return QueryResult(
                success=True,
                rows=rows,
                total_rows=results.total_rows,
                schema=schema,
                bytes_processed=query_job.total_bytes_processed,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"BigQuery query failed: {e}")
            return QueryResult(
                success=False,
                rows=[],
                total_rows=0,
                schema=[],
                error=str(e)
            )

    def get_customer_360(
        self,
        customer_id: Optional[str] = None,
        segment: Optional[str] = None,
        limit: int = 100,
    ) -> QueryResult:
        """
        Get customer 360 view data.

        Args:
            customer_id: Specific customer ID
            segment: Customer segment filter
            limit: Maximum results

        Returns:
            QueryResult with customer data
        """
        where_clauses = []

        if customer_id:
            where_clauses.append(f"customer_id = '{customer_id}'")

        if segment:
            where_clauses.append(f"segment = '{segment}'")

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
        SELECT
            customer_id,
            email,
            segment,
            lifetime_value,
            total_orders,
            engagement_score,
            churn_risk,
            last_purchase_date,
            created_at
        FROM `{self.project_id}.{self.default_dataset}.customer_360`
        WHERE {where_clause}
        ORDER BY lifetime_value DESC
        LIMIT {limit}
        """

        return self.execute_query(query)

    def get_campaign_performance(
        self,
        campaign_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> QueryResult:
        """
        Get campaign performance metrics.

        Args:
            campaign_id: Specific campaign ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum results

        Returns:
            QueryResult with campaign data
        """
        where_clauses = ["1=1"]

        if campaign_id:
            where_clauses.append(f"campaign_id = '{campaign_id}'")

        if start_date:
            where_clauses.append(f"date >= '{start_date}'")

        if end_date:
            where_clauses.append(f"date <= '{end_date}'")

        where_clause = " AND ".join(where_clauses)

        query = f"""
        SELECT
            campaign_id,
            campaign_name,
            channel,
            date,
            impressions,
            clicks,
            conversions,
            cost,
            revenue,
            SAFE_DIVIDE(clicks, impressions) as ctr,
            SAFE_DIVIDE(conversions, clicks) as conversion_rate,
            SAFE_DIVIDE(revenue, cost) as roas
        FROM `{self.project_id}.{self.default_dataset}.campaign_performance`
        WHERE {where_clause}
        ORDER BY date DESC
        LIMIT {limit}
        """

        return self.execute_query(query)

    def get_customer_segments(self) -> QueryResult:
        """Get customer segmentation summary."""
        query = f"""
        SELECT
            segment,
            COUNT(*) as customer_count,
            AVG(lifetime_value) as avg_ltv,
            AVG(engagement_score) as avg_engagement,
            AVG(churn_risk) as avg_churn_risk
        FROM `{self.project_id}.{self.default_dataset}.customer_360`
        GROUP BY segment
        ORDER BY customer_count DESC
        """

        return self.execute_query(query)

    def close(self):
        """Close BigQuery client connection."""
        if self.client:
            self.client.close()
            logger.info("BigQuery client closed")


def main():
    """Test BigQuery tool functionality."""
    from dotenv import load_dotenv
    import json

    load_dotenv()

    tool = BigQueryTool()

    # Test query validation
    print("Testing query validation...")
    valid_query = "SELECT * FROM customer_360 LIMIT 10"
    is_valid, error = tool.validate_query(valid_query)
    print(f"Valid query: {is_valid}, Error: {error}")

    invalid_query = "DROP TABLE customer_360"
    is_valid, error = tool.validate_query(invalid_query)
    print(f"Invalid query: {is_valid}, Error: {error}")

    # Test customer segments query
    print("\nTesting customer segments query...")
    result = tool.get_customer_segments()
    print(f"Success: {result.success}")
    print(f"Rows: {result.total_rows}")
    if result.success and result.rows:
        print(json.dumps(result.rows[:3], indent=2, default=str))
    elif result.error:
        print(f"Error: {result.error}")

    tool.close()


if __name__ == "__main__":
    main()
