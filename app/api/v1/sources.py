"""
Sources API Endpoint

Data source information and status.
"""

from flask import Blueprint, jsonify

from app.models import IngestionJob, SourceSyncState


sources_bp = Blueprint('sources', __name__)


# Source registry
SOURCES = {
    'offeneregister': {
        'name': 'OffeneRegister.de',
        'description': 'German company register backbone',
        'trust_score': 0.95,
        'enabled': True,
    },
    'opencorporates': {
        'name': 'OpenCorporates',
        'description': 'Global company data enrichment',
        'trust_score': 0.75,
        'enabled': True,
    },
    'gleif': {
        'name': 'GLEIF',
        'description': 'Legal Entity Identifier registry',
        'trust_score': 0.90,
        'enabled': True,
    },
    'openownership': {
        'name': 'OpenOwnership',
        'description': 'Beneficial ownership data (BODS)',
        'trust_score': 0.80,
        'enabled': True,
    },
    'opensanctions': {
        'name': 'OpenSanctions',
        'description': 'Sanctions and PEP screening',
        'trust_score': 0.85,
        'enabled': True,
    },
    'openlegaldata': {
        'name': 'OpenLegalData',
        'description': 'Legal context and court decisions',
        'trust_score': 0.60,
        'enabled': True,
    },
    'govdata': {
        'name': 'GovData',
        'description': 'German open government data',
        'trust_score': 0.40,
        'enabled': True,
    },
    'osm': {
        'name': 'OpenStreetMap',
        'description': 'Geospatial enrichment',
        'trust_score': 0.50,
        'enabled': True,
    },
}


@sources_bp.route('', methods=['GET'])
def list_sources():
    """List all data sources with status."""
    from app.core.extensions import db
    from app.models import CompanySourceRecord
    
    sources_list = []
    
    for key, source in SOURCES.items():
        # Get sync state
        sync_state = SourceSyncState.query.filter_by(source=key).first()
        
        # Get record count
        count = db.session.query(CompanySourceRecord).filter_by(source=key).count()
        
        sources_list.append({
            'id': key,
            'name': source['name'],
            'description': source['description'],
            'trust_score': source['trust_score'],
            'enabled': source['enabled'],
            'record_count': count,
            'last_sync': sync_state.last_sync_at.isoformat() if sync_state and sync_state.last_sync_at else None,
            'sync_status': sync_state.sync_status if sync_state else 'never',
        })
    
    return jsonify({
        'total': len(sources_list),
        'sources': sources_list,
    })


@sources_bp.route('/<source_name>', methods=['GET'])
def get_source(source_name: str):
    """Get details for a specific source."""
    if source_name not in SOURCES:
        return jsonify({'error': 'Source not found'}), 404
    
    source = SOURCES[source_name]
    sync_state = SourceSyncState.query.filter_by(source=source_name).first()
    
    return jsonify({
        'id': source_name,
        'name': source['name'],
        'description': source['description'],
        'trust_score': source['trust_score'],
        'enabled': source['enabled'],
        'sync_state': sync_state.to_dict() if sync_state else None,
    })


@sources_bp.route('/<source_name>/stats', methods=['GET'])
def get_source_stats(source_name: str):
    """Get statistics for a source."""
    if source_name not in SOURCES:
        return jsonify({'error': 'Source not found'}), 404
    
    from app.core.extensions import db
    from app.models import CompanySourceRecord, Company
    
    # Get record count
    record_count = db.session.query(CompanySourceRecord).filter_by(
        source=source_name
    ).count()
    
    # Get unique company count
    company_count = db.session.query(Company).join(CompanySourceRecord).filter(
        CompanySourceRecord.source == source_name
    ).count()
    
    # Get latest sync
    sync_state = SourceSyncState.query.filter_by(source=source_name).first()
    
    return jsonify({
        'source': source_name,
        'total_records': record_count,
        'unique_companies': company_count,
        'last_sync': sync_state.last_sync_at.isoformat() if sync_state and sync_state.last_sync_at else None,
    })