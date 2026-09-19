-- CivicMind AI — PostgreSQL Initialization SQL
-- Enables PostGIS and pgvector extensions at database creation time

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
