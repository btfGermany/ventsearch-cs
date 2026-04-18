"""
Admin API Endpoint

Admin operations for ingestion and management.
"""

from flask import Blueprint, jsonify, request
import uuid as uuid_module

from app.core.extensions import db
from app.models import IngestionJob, EntityMatchReview, Company


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/ingest/<source_name>', methods=['POST'])
def trigger_ingest(source_name: str):
    """Trigger ingestion for a source."""
    from app.tasks.ingestion_tasks import run_ingestion
    
    # Create job record
    job = IngestionJob(
        job_id=str(uuid_module.uuid4()),
        job_type='FULL_INGEST',
        source=source_name,
        status='pending',
    )
    db.session.add(job)
    db.session.commit()
    
    # Trigger Celery task
    run_ingestion.delay(source_name)
    
    return jsonify({
        'job_id': job.job_id,
        'status': 'triggered',
    })


@admin_bp.route('/reindex', methods=['POST'])
def trigger_reindex():
    """Trigger full reindex of data."""
    from app.tasks.indexing_tasks import run_reindex
    
    job = IngestionJob(
        job_id=str(uuid_module.uuid4()),
        job_type='REINDEX',
        status='pending',
    )
    db.session.add(job)
    db.session.commit()
    
    run_reindex.delay()
    
    return jsonify({
        'job_id': job.job_id,
        'status': 'triggered',
    })


@admin_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List ingestion jobs."""
    status = request.args.get('status')
    job_type = request.args.get('job_type')
    limit = request.args.get('limit', 50, type=int)
    
    query = IngestionJob.query
    
    if status:
        query = query.filter(IngestionJob.status == status)
    
    if job_type:
        query = query.filter(IngestionJob.job_type == job_type)
    
    jobs = query.order_by(IngestionJob.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'total': len(jobs),
        'jobs': [j.to_dict() for j in jobs],
    })


@admin_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id: str):
    """Get a specific job."""
    job = IngestionJob.query.filter_by(job_id=job_id).first()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict())


@admin_bp.route('/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id: str):
    """Retry a failed job."""
    job = IngestionJob.query.filter_by(job_id=job_id).first()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status != 'failed':
        return jsonify({'error': 'Only failed jobs can be retried'}), 400
    
    # Trigger task
    from app.tasks.ingestion_tasks import run_ingestion
    
    job.status = 'pending'
    job.retries += 1
    db.session.commit()
    
    run_ingestion.delay(job.source)
    
    return jsonify({
        'job_id': job.job_id,
        'status': 'retry_triggered',
    })


@admin_bp.route('/reviews', methods=['GET'])
def list_reviews():
    """List entity match reviews."""
    decision = request.args.get('decision')
    limit = request.args.get('limit', 50, type=int)
    
    query = EntityMatchReview.query
    
    if decision:
        query = query.filter(EntityMatchReview.decision == decision)
    else:
        query = query.filter(EntityMatchReview.decision == None)
    
    reviews = query.order_by(EntityMatchReview.match_score.desc()).limit(limit).all()
    
    return jsonify({
        'total': len(reviews),
        'reviews': [r.to_dict() for r in reviews],
    })


@admin_bp.route('/reviews/<int:review_id>/decide', methods=['POST'])
def decide_review(review_id: int):
    """Decide on a match review."""
    review = db.session.get(EntityMatchReview, review_id)
    
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    
    data = request.get_json() or {}
    decision = data.get('decision')
    
    if decision not in ['merge', 'keep_separate', 'needs_investigation']:
        return jsonify({'error': 'Invalid decision'}), 400
    
    review.decision = decision
    review.review_notes = data.get('notes')
    review.reviewed_by = data.get('reviewed_by', 'api')
    review.reviewed_at = db.func.now()
    
    # If merge, handle merging
    if decision == 'merge':
        from app.services.matching import MatchingService
        service = MatchingService()
        
        company_a = db.session.get(Company, review.company_a_id)
        company_b = db.session.get(Company, review.company_b_id)
        
        if company_a and company_b:
            service.merge_companies(company_a, company_b)
    
    db.session.commit()
    
    return jsonify(review.to_dict())


@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    from app.models import Company, CompanySourceRecord, SanctionsMatch
    
    # Company counts by status
    status_counts = db.session.query(
        Company.status, db.func.count(Company.id)
    ).group_by(Company.status).all()
    
    # Record counts by source
    source_counts = db.session.query(
        CompanySourceRecord.source, db.func.count(CompanySourceRecord.id)
    ).group_by(CompanySourceRecord.source).all()
    
    # Pending reviews
    pending_reviews = EntityMatchReview.query.filter(
        EntityMatchReview.decision == None
    ).count()
    
    # Pending sanctions matches
    pending_sanctions = SanctionsMatch.query.filter(
        SanctionsMatch.review_status == 'pending'
    ).count()
    
    return jsonify({
        'companies': {
            'total': Company.query.count(),
            'by_status': {s: c for s, c in status_counts},
        },
        'source_records': {
            'total': CompanySourceRecord.query.count(),
            'by_source': {s: c for s, c in source_counts},
        },
        'pending_reviews': pending_reviews,
        'pending_sanctions': pending_sanctions,
        'jobs': {
            'running': IngestionJob.query.filter_by(status='running').count(),
            'failed': IngestionJob.query.filter_by(status='failed').count(),
        },
    })