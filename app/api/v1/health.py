"""
Health Check API Endpoint

Provides system health information.
"""

from flask import Blueprint, jsonify, current_app


health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Return system health status."""
    health = {
        'status': 'healthy',
        'service': 'company-intel-aggregator',
        'version': current_app.config.get('API_VERSION', 'v1'),
    }
    
    # Check database
    try:
        from app.core.extensions import db
        db.session.execute(db.text('SELECT 1'))
        health['database'] = 'connected'
    except Exception as e:
        health['database'] = f'error: {str(e)}'
        health['status'] = 'degraded'
    
    # Check OpenSearch
    try:
        from app.services.search import SearchService
        if hasattr(current_app, 'opensearch') and current_app.opensearch.is_available:
            health['opensearch'] = 'connected'
        else:
            health['opensearch'] = 'not_configured'
    except Exception as e:
        health['opensearch'] = f'error: {str(e)}'
    
    # Check Celery
    try:
        from app.core.extensions import celery
        inspect = celery.control.inspect()
        stats = inspect.stats()
        if stats:
            health['celery'] = 'connected'
        else:
            health['celery'] = 'no_workers'
    except Exception as e:
        health['celery'] = f'error: {str(e)}'
    
    status_code = 200 if health['status'] == 'healthy' else 503
    
    return jsonify(health), status_code


@health_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint."""
    return jsonify({'pong': True})