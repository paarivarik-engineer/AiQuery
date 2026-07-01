#!/usr/bin/env python3
"""
Explore a PostgreSQL database schema (e.g. AWS RDS).

Usage:
  # Via environment variables (recommended)
  export AWS_DB_HOST=your-instance.region.rds.amazonaws.com
  export AWS_DB_PORT=5432
  export AWS_DB_NAME=your_database
  export AWS_DB_USER=your_user
  export AWS_DB_PASSWORD=your_password
  export AWS_DB_SSLMODE=require   # optional, default: require
  python scripts/explore_db.py

  # Or via a single DATABASE_URL
  export DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
  python scripts/explore_db.py

  # Output options
  python scripts/explore_db.py --format markdown -o schema_report.md
  python scripts/explore_db.py --format json -o schema.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import quote_plus, urlparse, parse_qs

import psycopg2
from psycopg2.extras import RealDictCursor


def build_connection_params() -> dict:
    """Build connection parameters from env vars or DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        parsed = urlparse(database_url)
        params = {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "dbname": parsed.path.lstrip("/"),
            "user": parsed.username,
            "password": parsed.password,
        }
        query = parse_qs(parsed.query)
        if "sslmode" in query:
            params["sslmode"] = query["sslmode"][0]
        return {k: v for k, v in params.items() if v}

    host = os.environ.get("AWS_DB_HOST") or os.environ.get("DB_HOST")
    if not host:
        return {}

    return {
        "host": host,
        "port": int(os.environ.get("AWS_DB_PORT") or os.environ.get("DB_PORT") or 5432),
        "dbname": os.environ.get("AWS_DB_NAME") or os.environ.get("DB_NAME"),
        "user": os.environ.get("AWS_DB_USER") or os.environ.get("DB_USER"),
        "password": os.environ.get("AWS_DB_PASSWORD") or os.environ.get("DB_PASSWORD"),
        "sslmode": os.environ.get("AWS_DB_SSLMODE") or os.environ.get("DB_SSLMODE") or "require",
    }


def connect(params: dict):
    """Open a PostgreSQL connection."""
    return psycopg2.connect(**params, cursor_factory=RealDictCursor)


def fetch_server_info(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT version() AS version, current_database() AS database, current_user AS user")
        row = cur.fetchone()
        cur.execute("SELECT inet_server_addr() AS server_ip, inet_server_port() AS server_port")
        network = cur.fetchone()
        return {**row, **network}


def fetch_schemas(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
              AND schema_name NOT LIKE 'pg_temp_%'
              AND schema_name NOT LIKE 'pg_toast_temp_%'
            ORDER BY schema_name
        """)
        return [r["schema_name"] for r in cur.fetchall()]


def fetch_tables(conn, schema: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                t.table_name,
                pg_total_relation_size(quote_ident(t.table_schema) || '.' || quote_ident(t.table_name)) AS size_bytes,
                obj_description((quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass) AS comment
            FROM information_schema.tables t
            WHERE t.table_schema = %s AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
        """, (schema,))
        tables = cur.fetchall()

        for table in tables:
            cur.execute(f"""
                SELECT COUNT(*) AS row_count FROM {schema}.{table['table_name']}
            """)
            table["row_count"] = cur.fetchone()["row_count"]

        return tables


def fetch_columns(conn, schema: str, table: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                c.column_name,
                c.ordinal_position,
                c.data_type,
                c.udt_name,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.is_nullable,
                c.column_default,
                pgd.description AS comment
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_statio_all_tables st
                ON st.schemaname = c.table_schema AND st.relname = c.table_name
            LEFT JOIN pg_catalog.pg_description pgd
                ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """, (schema, table))
        return cur.fetchall()


def fetch_primary_keys(conn, schema: str, table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = %s AND tc.table_name = %s
            ORDER BY kcu.ordinal_position
        """, (schema, table))
        return [r["column_name"] for r in cur.fetchall()]


def fetch_foreign_keys(conn, schema: str, table: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_schema,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = %s AND tc.table_name = %s
            ORDER BY tc.constraint_name, kcu.ordinal_position
        """, (schema, table))
        return cur.fetchall()


def fetch_indexes(conn, schema: str, table: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
            ORDER BY indexname
        """, (schema, table))
        return cur.fetchall()


def explore_database(params: dict) -> dict:
    """Collect full schema metadata from the database."""
    with connect(params) as conn:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "connection": {
                "host": params.get("host"),
                "port": params.get("port"),
                "database": params.get("dbname"),
                "user": params.get("user"),
                "sslmode": params.get("sslmode"),
            },
            "server": fetch_server_info(conn),
            "schemas": {},
        }

        for schema in fetch_schemas(conn):
            schema_data = {"tables": {}}
            for table_info in fetch_tables(conn, schema):
                table_name = table_info["table_name"]
                schema_data["tables"][table_name] = {
                    "row_count": table_info["row_count"],
                    "size_bytes": table_info["size_bytes"],
                    "comment": table_info["comment"],
                    "columns": fetch_columns(conn, schema, table_name),
                    "primary_key": fetch_primary_keys(conn, schema, table_name),
                    "foreign_keys": fetch_foreign_keys(conn, schema, table_name),
                    "indexes": fetch_indexes(conn, schema, table_name),
                }
            report["schemas"][schema] = schema_data

        return report


def format_type(col: dict) -> str:
    dtype = col["data_type"]
    if col["character_maximum_length"]:
        return f"{dtype}({col['character_maximum_length']})"
    if col["numeric_precision"]:
        scale = col["numeric_scale"]
        return f"{dtype}({col['numeric_precision']},{scale})" if scale else f"{dtype}({col['numeric_precision']})"
    return col["udt_name"] or dtype


def to_markdown(report: dict) -> str:
    lines = [
        "# Database Schema Report",
        "",
        f"**Generated:** {report['generated_at']}",
        "",
        "## Server Info",
        "",
        f"- **Version:** {report['server']['version']}",
        f"- **Database:** {report['server']['database']}",
        f"- **User:** {report['server']['user']}",
        f"- **Host:** {report['connection']['host']}:{report['connection']['port']}",
        "",
    ]

    for schema_name, schema_data in report["schemas"].items():
        lines.append(f"## Schema: `{schema_name}`")
        lines.append("")
        for table_name, table in schema_data["tables"].items():
            size_mb = (table["size_bytes"] or 0) / (1024 * 1024)
            lines.append(f"### Table: `{schema_name}.{table_name}`")
            lines.append("")
            lines.append(f"- **Rows:** {table['row_count']:,}")
            lines.append(f"- **Size:** {size_mb:.2f} MB")
            if table["comment"]:
                lines.append(f"- **Comment:** {table['comment']}")
            if table["primary_key"]:
                lines.append(f"- **Primary Key:** {', '.join(table['primary_key'])}")
            lines.append("")
            lines.append("| Column | Type | Nullable | Default |")
            lines.append("|--------|------|----------|---------|")
            for col in table["columns"]:
                nullable = "YES" if col["is_nullable"] == "YES" else "NO"
                default = (col["column_default"] or "").replace("|", "\\|")
                lines.append(f"| {col['column_name']} | {format_type(col)} | {nullable} | {default} |")

            if table["foreign_keys"]:
                lines.append("")
                lines.append("**Foreign Keys:**")
                for fk in table["foreign_keys"]:
                    lines.append(
                        f"- `{fk['column_name']}` → `{fk['foreign_schema']}.{fk['foreign_table']}.{fk['foreign_column']}`"
                    )

            if table["indexes"]:
                lines.append("")
                lines.append("**Indexes:**")
                for idx in table["indexes"]:
                    lines.append(f"- `{idx['indexname']}`: `{idx['indexdef']}`")

            lines.append("")

    return "\n".join(lines)


def test_connection(params: dict) -> bool:
    """Quick connectivity check."""
    try:
        with connect(params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except psycopg2.Error as exc:
        print(f"Connection failed: {exc}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Explore a PostgreSQL database schema")
    parser.add_argument("--test", action="store_true", help="Only test connectivity")
    parser.add_argument("--format", choices=["json", "markdown", "summary"], default="summary")
    parser.add_argument("-o", "--output", help="Write report to file instead of stdout")
    parser.add_argument("--schema", help="Limit exploration to a single schema")
    args = parser.parse_args()

    params = build_connection_params()
    required = ["host", "dbname", "user", "password"]
    missing = [k for k in required if not params.get(k)]
    if missing:
        print("Missing connection details. Set DATABASE_URL or these env vars:", file=sys.stderr)
        for key in missing:
            env_name = f"AWS_DB_{key.upper()}" if key != "dbname" else "AWS_DB_NAME"
            print(f"  - {env_name}", file=sys.stderr)
        sys.exit(1)

    if args.test:
        sys.exit(0 if test_connection(params) else 1)

    print(f"Connecting to {params['host']}:{params.get('port', 5432)}/{params['dbname']}...", file=sys.stderr)
    report = explore_database(params)

    if args.schema:
        report["schemas"] = {k: v for k, v in report["schemas"].items() if k == args.schema}

    if args.format == "json":
        output = json.dumps(report, indent=2, default=str)
    elif args.format == "markdown":
        output = to_markdown(report)
    else:
        table_count = sum(len(s["tables"]) for s in report["schemas"].values())
        output = (
            f"Connected to: {report['server']['database']} ({report['server']['version'][:60]}...)\n"
            f"Schemas: {len(report['schemas'])}\n"
            f"Tables: {table_count}\n"
        )
        for schema_name, schema_data in report["schemas"].items():
            output += f"\n  [{schema_name}]\n"
            for table_name, table in schema_data["tables"].items():
                output += f"    - {table_name} ({table['row_count']:,} rows, {len(table['columns'])} cols)\n"

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
