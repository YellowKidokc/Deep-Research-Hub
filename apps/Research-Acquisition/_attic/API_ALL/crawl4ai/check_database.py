#!/usr/bin/env python3
"""Check what's in the PostgreSQL database."""

import psycopg2

conn = psycopg2.connect(
    host='192.168.1.177',
    port=2665,
    dbname='theophysics',
    user='Yellowkid',
    password='Moss9pep28$'
)

cur = conn.cursor()

# Check schemas
print("=== SCHEMAS ===")
cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
schemas = cur.fetchall()
for s in schemas:
    print(f"  - {s[0]}")

print("\n=== TABLES IN 'public' ===")
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = cur.fetchall()
for t in tables:
    print(f"  - {t[0]}")

# Check if 'axioms' schema exists
print("\n=== CHECKING FOR 'axioms' SCHEMA ===")
cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'axioms'")
axioms_schema = cur.fetchone()
if axioms_schema:
    print("  Found 'axioms' schema!")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'axioms'")
    axiom_tables = cur.fetchall()
    print(f"  Tables in 'axioms' schema:")
    for t in axiom_tables:
        print(f"    - {t[0]}")
else:
    print("  No 'axioms' schema found")
    
# Check all tables for anything with 'axiom' in the name
print("\n=== SEARCHING FOR 'axiom' IN TABLE NAMES ===")
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name LIKE '%axiom%' OR table_name LIKE '%canonical%'
    ORDER BY table_schema, table_name
""")
matching = cur.fetchall()
if matching:
    for m in matching:
        print(f"  - {m[0]}.{m[1]}")
else:
    print("  (none found)")

conn.close()
