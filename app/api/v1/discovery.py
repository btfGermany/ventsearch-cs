"""
Discovery API Endpoint

Dataset discovery and catalog operations.
"""

from flask import Blueprint, jsonify, request

from app.models import DatasetCatalogItem, DatasetResource
from app.services.discovery.crawler import DiscoveryCrawler


discovery_bp = Blueprint('discovery', __name__)


@discovery_bp.route('/datasets', methods=['GET'])
def list_datasets():
    """List discovered datasets with filters."""
    relevance = request.args.get('relevance')
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 25, type=int), 100)
    
    query = DatasetCatalogItem.query
    
    if relevance:
        query = query.filter(DatasetCatalogItem.relevance == relevance)
    
    # Count
    total = query.count()
    
    # Paginate
    datasets = query.order_by(DatasetCatalogItem.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    return jsonify({
        'total': total,
        'page': page,
        'page_size': page_size,
        'datasets': [d.to_dict() for d in datasets],
    })


@discovery_bp.route('/datasets/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id: int):
    """Get a specific dataset."""
    dataset = db.session.get(DatasetCatalogItem, dataset_id)
    
    if not dataset:
        return jsonify({'error': 'Dataset not found'}), 404
    
    result = dataset.to_dict()
    result['resources'] = [r.to_dict() for r in dataset.resources]
    
    return jsonify(result)


@discovery_bp.route('/datasets/<int:dataset_id>/resources', methods=['GET'])
def get_dataset_resources(dataset_id: int):
    """Get resources for a dataset."""
    dataset = db.session.get(DatasetCatalogItem, dataset_id)
    
    if not dataset:
        return jsonify({'error': 'Dataset not found'}), 404
    
    resources = [r.to_dict() for r in dataset.resources]
    
    return jsonify({
        'dataset_id': dataset_id,
        'total': len(resources),
        'resources': resources,
    })


@discovery_bp.route('/datasets/relevant', methods=['GET'])
def get_relevant_datasets():
    """Get datasets relevant for company data."""
    datasets = DatasetCatalogItem.query.filter(
        DatasetCatalogItem.relevance.in_(['directly_relevant', 'indirectly_relevant'])
    ).order_by(
        DatasetCatalogItem.relevance.desc(),
        DatasetCatalogItem.created_at.desc()
    ).limit(50).all()
    
    # Group by relevance
    relevant = {'directly': [], 'indirectly': []}
    
    for dataset in datasets:
        d = dataset.to_dict()
        if dataset.relevance == 'directly_relevant':
            relevant['directly'].append(d)
        else:
            relevant['indirectly'].append(d)
    
    return jsonify({
        'total': len(datasets),
        'datasets': relevant,
    })


# Import db for this module
from app.core.extensions import db