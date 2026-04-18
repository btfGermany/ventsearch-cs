"""
Screening API Endpoint

Sanctions and risk screening operations.
"""

from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields

from app.core.extensions import db
from app.models import Company, SanctionsMatch


screening_bp = Blueprint('screening', __name__)


@screening_bp.route('/match', methods=['POST'])
def screen_match():
    """Screen a company against sanctions."""
    data = request.get_json() or {}
    company_id = data.get('company_id')
    
    if not company_id:
        return jsonify({'error': 'company_id required'}), 400
    
    # Get company
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Run screening
    from app.services.screening import ScreeningService
    service = ScreeningService()
    results = service.screen_company(company)
    
    return jsonify({
        'company_id': company_id,
        'total_matches': len(results),
        'matches': results,
    })


@screening_bp.route('/search', methods=['GET'])
def search_sanctions():
    """Search sanctions entities."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    from app.models import SanctionsEntity
    
    # Search
    entities = SanctionsEntity.query.filter(
        SanctionsEntity.name.ilike(f'%{query}%'),
        SanctionsEntity.is_designated == True
    ).limit(20).all()
    
    return jsonify({
        'query': query,
        'total': len(entities),
        'entities': [e.to_dict() for e in entities],
    })


@screening_bp.route('/matches', methods=['GET'])
def list_sanctions_matches():
    """List all sanctions matches with filters."""
    review_status = request.args.get('review_status')
    min_score = request.args.get('min_score', 0.7, type=float)
    
    query = SanctionsMatch.query
    
    if review_status:
        query = query.filter(SanctionsMatch.review_status == review_status)
    
    if min_score:
        query = query.filter(SanctionsMatch.match_score >= min_score)
    
    matches = query.order_by(SanctionsMatch.match_score.desc()).limit(100).all()
    
    return jsonify({
        'total': len(matches),
        'matches': [m.to_dict() for m in matches],
    })


@screening_bp.route('/matches/<int:match_id>', methods=['GET'])
def get_match(match_id: int):
    """Get a specific sanctions match."""
    match = db.session.get(SanctionsMatch, match_id)
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    result = match.to_dict()
    result['company'] = match.company.to_dict() if match.company else None
    result['sanctions_entity'] = match.sanctions_entity.to_dict() if match.sanctions_entity else None
    
    return jsonify(result)


@screening_bp.route('/matches/<int:match_id>/review', methods=['POST'])
def review_match(match_id: int):
    """Review a sanctions match."""
    match = db.session.get(SanctionsMatch, match_id)
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    data = request.get_json() or {}
    match.review_status = data.get('decision', match.review_status)
    match.review_notes = data.get('notes', match.review_notes)
    match.reviewed_by = data.get('reviewed_by', 'api')
    match.reviewed_at = db.func.now()
    
    db.session.commit()
    
    return jsonify(match.to_dict())