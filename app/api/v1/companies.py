"""
Companies API Endpoint

REST API for company operations.
"""

from flask import Blueprint, jsonify, request, current_app
from marshmallow import Schema, fields, validate, validates_schema, ValidationError

from app.core.extensions import db
from app.core.errors import NotFoundError
from app.models import (
    Company, CompanyName, CompanyIdentifier, CompanyAddress,
    CompanySourceRecord, CompanyEvent
)


companies_bp = Blueprint('companies', __name__)


class CompanySchema(Schema):
    """Company schema."""
    id = fields.Int(dump_only=True)
    uuid = fields.Str(dump_only=True)
    status = fields.Str()
    canonical_name = fields.Str()
    legal_form = fields.Str()
    country = fields.Str()
    registration_number = fields.Str()
    registration_court = fields.Str()
    registration_date = fields.Date()
    lei = fields.Str()
    industry_code = fields.Str()
    confidence_score = fields.Float(dump_only=True)
    is_verified = fields.Bool()
    primary_city = fields.Str()
    primary_postal_code = fields.Str()


class CompanyDetailSchema(CompanySchema):
    """Detailed company with relationships."""
    names = fields.Nested('CompanyNameSchema', many=True, dump_only=True)
    identifiers = fields.Nested('CompanyIdentifierSchema', many=True, dump_only=True)
    addresses = fields.Nested('CompanyAddressSchema', many=True, dump_only=True)
    source_records = fields.Nested('CompanySourceRecordSchema', many=True, dump_only=True)


class CompanyNameSchema(Schema):
    """Company name schema."""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    name_type = fields.Str()
    is_primary = fields.Bool()
    is_current = fields.Bool()
    language = fields.Str()
    source = fields.Str(dump_only=True)


class CompanyIdentifierSchema(Schema):
    """Company identifier schema."""
    id = fields.Int(dump_only=True)
    identifier_type = fields.Str()
    identifier_value = fields.Str()
    issuing_authority = fields.Str()
    is_primary = fields.Bool()
    source = fields.Str(dump_only=True)


class CompanyAddressSchema(Schema):
    """Company address schema."""
    id = fields.Int(dump_only=True)
    address_type = fields.Str()
    street = fields.Str()
    house_number = fields.Str()
    postal_code = fields.Str()
    city = fields.Str()
    region = fields.Str()
    country = fields.Str()
    is_primary = fields.Bool()
    latitude = fields.Float()
    longitude = fields.Float()
    source = fields.Str(dump_only=True)


class CompanySourceRecordSchema(Schema):
    """Company source record schema."""
    id = fields.Int(dump_only=True)
    source = fields.Str(dump_only=True)
    source_record_id = fields.Str(dump_only=True)
    last_synced = fields.DateTime(dump_only=True)


# Pagination schema
class PaginationSchema(Schema):
    """Pagination parameters."""
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=25, validate=validate.Range(min=1, max=100))


@companies_bp.route('', methods=['GET'])
def list_companies():
    """List companies with pagination."""
    # Parse pagination
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 25, type=int), 100)
    
    # Parse filters
    filters = {}
    if request.args.get('country'):
        filters['country'] = request.args.get('country')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('city'):
        filters['primary_city'] = request.args.get('city')
    
    # Build query
    query = Company.query.filter(Company.is_merged == False)
    
    for key, value in filters.items():
        if hasattr(Company, key):
            query = query.filter(getattr(Company, key) == value)
    
    # Count
    total = query.count()
    
    # Paginate
    companies = query.order_by(Company.created_at.desc()) \
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


@companies_bp.route('/<int:company_id>', methods=['GET'])
def get_company(company_id: int):
    """Get company by ID."""
    company = db.session.get(Company, company_id)
    
    if not company:
        raise NotFoundError('Company', str(company_id))
    
    include_relations = request.args.get('include_relations', 'false').lower() == 'true'
    
    return jsonify(company.to_dict(include_relations=include_relations))


@companies_bp.route('/<int:company_id>/identifiers', methods=['GET'])
def get_company_identifiers(company_id: int):
    """Get company identifiers."""
    company = db.session.get(Company, company_id)
    
    if not company:
        raise NotFoundError('Company', str(company_id))
    
    identifiers = [i.to_dict() for i in company.identifiers]
    
    return jsonify({
        'company_id': company_id,
        'total': len(identifiers),
        'identifiers': identifiers,
    })


@companies_bp.route('/<int:company_id>/addresses', methods=['GET'])
def get_company_addresses(company_id: int):
    """Get company addresses."""
    company = db.session.get(Company, company_id)
    
    if not company:
        raise NotFoundError('Company', str(company_id))
    
    addresses = [a.to_dict() for a in company.addresses]
    
    return jsonify({
        'company_id': company_id,
        'total': len(addresses),
        'addresses': addresses,
    })


@companies_bp.route('/<int:company_id>/ownership', methods=['GET'])
def get_company_ownership(company_id: int):
    """Get company ownership data."""
    company = db.session.get(Company, company_id)
    
    if not company:
        raise NotFoundError('Company', str(company_id))
    
    from app.models import OwnershipStatement
    
    # Get ownership statements where company is subject
    statements = OwnershipStatement.query.filter(
        OwnershipStatement.subject_name.ilike(f'%{company.canonical_name}%')
    ).order_by(OwnershipStatement.publication_date.desc()).all()
    
    return jsonify({
        'company_id': company_id,
        'total': len(statements),
        'statements': [s.to_dict() for s in statements],
    })


@companies_bp.route('/<int:company_id>/sanctions', methods=['GET'])
def get_company_sanctions(company_id: int):
    """Get sanctions matches for company."""
    company = db.session.get(Company, company_id)
    
    if not company:
        raise NotFoundError('Company', str(company_id))
    
    from app.models import SanctionsMatch
    
    matches = SanctionsMatch.query.filter_by(company_id=company_id).all()
    
    return jsonify({
        'company_id': company_id,
        'total': len(matches),
        'matches': [m.to_dict() for m in matches],
    })


@companies_bp.route('/<int:company_id>/legal-context', methods=['GET'])
def get_company_legal(company_id: int):
    """Get legal references for company."""
    company = db.session.get(Company, company_id)
    
    if not company:
        raise NotFoundError('Company', str(company_id))
    
    # Simplified: placeholder for legal references
    # In production, would link to legal references via identifiers/addresses
    return jsonify({
        'company_id': company_id,
        'total': 0,
        'references': [],
    })


@companies_bp.route('/<int:company_id>/locations', methods=['GET'])
def get_company_locations(company_id: int):
    """Get geo locations for company."""
    company = db.session.get(Company, company_id)
    
    if not company:
        raise NotFoundError('Company', str(company_id))
    
    from app.models import GeoMatch
    
    matches = GeoMatch.query.filter_by(company_id=company_id).all()
    
    locations = []
    for match in matches:
        locations.append({
            'poi': match.poi.to_dict(),
            'match_score': match.match_score,
            'match_type': match.match_type,
        })
    
    return jsonify({
        'company_id': company_id,
        'total': len(locations),
        'locations': locations,
    })


@companies_bp.route('/uuid/<uuid>', methods=['GET'])
def get_company_by_uuid(uuid: str):
    """Get company by UUID."""
    company = Company.query.filter_by(uuid=uuid).first()
    
    if not company:
        raise NotFoundError('Company UUID', uuid)
    
    return jsonify(company.to_dict(include_relations=True))