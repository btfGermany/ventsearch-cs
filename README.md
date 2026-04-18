# Company Intelligence Aggregator Platform

A modular Flask-based platform for aggregating company data from multiple open and semi-open sources, focused primarily on German companies with international extensibility.

## Features

- **Multi-Source Ingestion**: Connectors for OffeneRegister, OpenCorporates, GLEIF, OpenOwnership, OpenSanctions, OpenLegalData, GovData, and OSM
- **Entity Resolution**: Deterministic and probabilistic matching with confidence scores
- **Knowledge Graph**: Company relationships, ownership, sanctions, legal context, geo data
- **Advanced Search**: Full-text search with filters and aggregations via OpenSearch
- **REST API**: Versioned API with JSON responses
- **Admin Interface**: German-language admin UI for monitoring and management
- **Background Jobs**: Celery-based ingestion and processing

## Quick Start

### Using Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

The web application will be available at http://localhost:5000
Admin UI at http://localhost:5000/admin/

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/company_intel

# Run migrations
flask db upgrade

# Start application
python run.py
```

## API Endpoints

### Companies

- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/<id>` - Get company details
- `GET /api/v1/companies/<id>/identifiers` - Company identifiers
- `GET /api/v1/companies/<id>/ownership` - Ownership data
- `GET /api/v1/companies/<id>/sanctions` - Sanctions matches
- `GET /api/v1/companies/<id>/locations` - Geo locations

### Search

- `GET /api/v1/companies/search?q=...` - Full-text search
- `POST /api/v1/query/advanced` - Structured query

### Sources

- `GET /api/v1/sources` - List data sources
- `GET /api/v1/sources/<source>/stats` - Source statistics

### Screening

- `POST /api/v1/screening/match` - Screen company
- `GET /api/v1/screening/matches` - List matches
- `GET /api/v1/screening/matches/<id>/review` - Review match

### Discovery

- `GET /api/v1/discovery/datasets` - List datasets

### Admin

- `POST /api/v1/admin/ingest/<source>` - Trigger ingestion
- `POST /api/v1/admin/reindex` - Trigger reindex
- `GET /api/v1/admin/jobs` - List jobs
- `GET /api/v1/admin/reviews` - List reviews

### Health

- `GET /api/v1/health` - Health check

## Triggering Ingestion

```bash
# Full ingestion for a source
curl -X POST http://localhost:5000/api/v1/admin/ingest/offeneregister

# Check job status
curl http://localhost:5000/api/v1/admin/jobs
```

## Database Model

Key entities:
- `Company` - Core company entity
- `CompanyName` - Names and aliases
- `CompanyIdentifier` - Identifiers (LEI, HRB, etc.)
- `CompanyAddress` - Addresses
- `CompanySourceRecord` - Source provenance
- `LEIRecord`, `LEIRelationship` - LEI data
- `OwnershipStatement` - BODS ownership
- `SanctionsEntity`, `SanctionsMatch` - Sanctions screening
- `GeoPointOfInterest` - OSM geo data

## Configuration

See `.env.example` for available environment variables.

Key settings:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENSEARCH_URL` - OpenSearch URL
- `LOG_LEVEL` - Logging level

## Architecture

```
app/
├── api/v1/          # REST API endpoints
├── admin/           # Admin UI routes/templates
├── core/            # Configuration, extensions, errors
├── models/           # SQLAlchemy models
├── schemas/         # Marshmallow schemas
├── services/        # Business logic
│   ├── matching/   # Entity resolution
│   ├── search/    # OpenSearch integration
│   └── screening/ # Sanctions screening
├── sources/        # Source connectors
│   ├── offeneregister/
│   ├── opencorporates/
│   ├── gleif/
│   └── ...
└── tasks/        # Celery tasks
```

## Testing

```bash
pytest tests/
```

## License

Internal use only.