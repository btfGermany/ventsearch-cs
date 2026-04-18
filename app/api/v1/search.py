"""
Search API Endpoint

Advanced company search with filters.
"""

from flask import Blueprint, jsonify, request

from app.models import Company
from app.services.search import SearchService


search_bp = Blueprint('search', __name__)


@search_bp.route('/companies/search', methods=['GET'])
def search_companies():
    """Search companies with full-text search and filters."""
    query = request.args.get('q', '')
    
    # Parse filters from query params
    filters = {}
    for key in ['country', 'status', 'legal_form', 'city', 'postal_code', 'industry_code', 'source', 'region']:
        value = request.args.get(key)
        if value:
            filters[key] = value
    
    # Boolean filters
    if request.args.get('has_lei'):
        filters['has_lei'] = True
    
    # Range filters
    if request.args.get('min_confidence'):
        filters['min_confidence'] = float(request.args.get('min_confidence'))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 25, type=int), 100)
    
    # Try OpenSearch first if available
    if hasattr(search_bp, 'search_service') and search_bp.search_service.is_available:
        results = search_bp.search_service.search(
            query=query,
            filters=filters,
            page=page,
            page_size=page_size,
        )
        return jsonify(results)
    
    # Fallback to database search
    return _db_search(query, filters, page, page_size)


def _db_search(query: str, filters: dict, page: int, page_size: int):
    """Database-based search fallback."""
    q = Company.query.filter(Company.is_merged == False)
    
    if query:
        q = q.filter(Company.canonical_name.ilike(f'%{query}%'))
    
    # Apply filters
    for key, value in filters.items():
        if hasattr(Company, key):
            q = q.filter(getattr(Company, key) == value)
    
    # Count
    total = q.count()
    
    # Paginate
    companies = q.order_by(Company.confidence_score.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    return jsonify({
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'companies': [c.to_dict() for c in companies],
    })


@search_bp.route('/query/advanced', methods=['POST'])
def advanced_query():
    """Advanced structured query endpoint."""
    from marshmallow import Schema, fields
    
    data = request.get_json() or {}
    query = data.get('query', '')
    filters = data.get('filters', {})
    page = data.get('page', 1)
    page_size = min(data.get('page_size', 25), 100)
    sort = data.get('sort', [{'field': 'confidence_score', 'order': 'desc'}])
    
    # Try OpenSearch first if available
    if hasattr(search_bp, 'search_service') and search_bp.search_service.is_available:
        sort_params = [{s['field']: {'order': s.get('order', 'desc')}} for s in sort]
        
        results = search_bp.search_service.search(
            query=query,
            filters=filters,
            page=page,
            page_size=page_size,
            sort=sort_params,
        )
        return jsonify(results)
    
    # Fallback
    return _db_search(query, filters, page, page_size)