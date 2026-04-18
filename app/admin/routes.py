"""
Admin UI Routes - Flask templates for administration.

German-language admin interface.
"""

from flask import Blueprint, render_template, jsonify, request

from app.core.extensions import db
from app.models import (
    Company, IngestionJob, SourceSyncState, EntityMatchReview, 
    SanctionsMatch, CompanySourceRecord
)


admin_ui_bp = Blueprint('admin_ui', __name__, template_folder='templates')


@admin_ui_bp.route('/', methods=['GET'])
def index():
    """Admin dashboard - Übersicht."""
    # Statistics
    company_count = Company.query.count()
    source_count = CompanySourceRecord.query.count()
    job_count = IngestionJob.query.count()
    pending_reviews = EntityMatchReview.query.filter(
        EntityMatchReview.decision == None
    ).count()
    pending_sanctions = SanctionsMatch.query.filter(
        SanctionsMatch.review_status == 'pending'
    ).count()
    
    # Recent jobs
    recent_jobs = IngestionJob.query.order_by(
        IngestionJob.created_at.desc()
    ).limit(10).all()
    
    return render_template('admin_index.html',
        company_count=company_count,
        source_count=source_count,
        job_count=job_count,
        pending_reviews=pending_reviews,
        pending_sanctions=pending_sanctions,
        recent_jobs=recent_jobs,
    )


@admin_ui_bp.route('/datenquellen', methods=['GET'])
def sources():
    """Data sources status - Datenquellen-Status."""
    sources = SourceSyncState.query.all()
    source_records = db.session.query(
        CompanySourceRecord.source, 
        db.func.count(CompanySourceRecord.id)
    ).group_by(CompanySourceRecord.source).all()
    
    sources_data = {}
    for source, count in source_records:
        sources_data[source] = count
    
    return render_template('admin_sources.html',
        sources=sources,
        source_records=sources_data,
    )


@admin_ui_bp.route('/jobs', methods=['GET'])
def jobs():
    """Job list - Letzte Ingestion-Jobs."""
    status_filter = request.args.get('status')
    
    query = IngestionJob.query
    if status_filter:
        query = query.filter(IngestionJob.status == status_filter)
    
    jobs = query.order_by(IngestionJob.created_at.desc()).limit(100).all()
    
    return render_template('admin_jobs.html',
        jobs=jobs,
        status_filter=status_filter,
    )


@admin_ui_bp.route('/fehler', methods=['GET'])
def errors():
    """Failed jobs - Fehlgeschlagene Jobs."""
    jobs = IngestionJob.query.filter_by(status='failed').order_by(
        IngestionJob.created_at.desc()
    ).limit(50).all()
    
    return render_template('admin_errors.html',
        jobs=jobs,
    )


@admin_ui_bp.route('/reviews', methods=['GET'])
def reviews():
    """Review queue - Review-Warteschlange."""
    reviews = EntityMatchReview.query.filter(
        EntityMatchReview.decision == None
    ).order_by(EntityMatchReview.match_score.desc()).all()
    
    # Get company data for each review
    reviews_data = []
    for review in reviews:
        company_a = db.session.get(Company, review.company_a_id)
        company_b = db.session.get(Company, review.company_b_id)
        
        reviews_data.append({
            'review': review,
            'company_a': company_a.to_dict() if company_a else None,
            'company_b': company_b.to_dict() if company_b else None,
        })
    
    return render_template('admin_reviews.html',
        reviews=reviews_data,
    )


@admin_ui_bp.route('/search', methods=['GET'])
def search():
    """Search test - Suchtest-Seite."""
    query = request.args.get('q', '')
    results = []
    total = 0
    
    if query:
        companies = Company.query.filter(
            Company.canonical_name.ilike(f'%{query}%')
        ).limit(50).all()
        
        total = len(companies)
        results = [c.to_dict() for c in companies]
    
    return render_template('admin_search.html',
        query=query,
        results=results,
        total=total,
    )


@admin_ui_bp.route('/status', methods=['GET'])
def health():
    """System health - Systemstatus / Health."""
    # Check services
    health_data = {
        'database': False,
        'opensearch': False,
        'celery': False,
    }
    
    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        health_data['database'] = True
    except:
        pass
    
    # OpenSearch
    try:
        from flask import current_app
        if hasattr(current_app, 'opensearch'):
            health_data['opensearch'] = current_app.opensearch.is_available
    except:
        pass
    
    return render_template('admin_health.html',
        health=health_data,
    )