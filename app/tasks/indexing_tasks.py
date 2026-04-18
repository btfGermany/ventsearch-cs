"""
Celery Indexing Tasks

Background tasks for indexing data to OpenSearch.
"""

import logging
import uuid
from datetime import datetime
from celery import shared_task


logger = logging.getLogger('company_intel.tasks.indexing')


def get_app():
    """Get Flask app instance for Celery context."""
    from app import create_app
    from app.core.config import get_config
    return create_app(get_config())


@shared_task(bind=True, max_retries=3)
def run_reindex(self):
    """Reindex all companies to OpenSearch."""
    from app.models import Company
    from app.services.search import SearchService
    from app.models import IngestionJob
    from app.core.extensions import db
    
    job_id = str(uuid.uuid4())
    app = get_app()
    
    with app.app_context():
        job = IngestionJob(
            job_id=job_id,
            job_type='REINDEX',
            status='running',
            started_at=datetime.utcnow(),
        )
        db.session.add(job)
        db.session.commit()
        
        logger.info("Starting reindex job")
        
        indexed = 0
        
        try:
            search_service = None
            
            if hasattr(app, 'opensearch'):
                search_service = app.opensearch.get_service()
            
            if not search_service or not search_service.is_available:
                logger.warning("OpenSearch not available, skipping reindex")
                job.status = 'completed'
                job.processed_items = 0
                job.completed_at = datetime.utcnow()
                db.session.commit()
                return {'indexed': 0}
            
            # Get all companies
            companies = Company.query.all()
            
            for company in companies:
                try:
                    doc = company.to_dict()
                    if search_service.index_company(doc):
                        indexed += 1
                except Exception as e:
                    logger.error(f"Failed to index company {company.id}: {e}")
            
            job.status = 'completed'
            job.processed_items = indexed
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Reindex complete: {indexed} companies indexed")
            
        except Exception as e:
            logger.error(f"Reindex job {job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            raise self.retry(exc=e, countdown=60)
    
    return {'indexed': indexed}


@shared_task
def index_company(company_id: int):
    """Index a single company."""
    from app.models import Company
    from app.services.search import SearchService
    from app.core.extensions import db
    
    app = get_app()
    
    with app.app_context():
        search_service = None
        
        if hasattr(app, 'opensearch'):
            search_service = app.opensearch.get_service()
        
        if not search_service or not search_service.is_available:
            return {'indexed': 0}
        
        company = db.session.get(Company, company_id)
        if not company:
            return {'indexed': 0}
        
        try:
            doc = company.to_dict()
            success = search_service.index_company(doc)
            return {'indexed': 1 if success else 0}
        except Exception as e:
            logger.error(f"Failed to index company {company_id}: {e}")
            return {'indexed': 0}


@shared_task
def delete_company(company_id: int):
    """Delete a company from the index."""
    from app.services.search import SearchService
    
    app = get_app()
    
    with app.app_context():
        search_service = None
        
        if hasattr(app, 'opensearch'):
            search_service = app.opensearch.get_service()
        
        if not search_service or not search_service.is_available:
            return {'deleted': 0}
        
        try:
            success = search_service.delete_company(company_id)
            return {'deleted': 1 if success else 0}
        except Exception as e:
            logger.error(f"Failed to delete company {company_id}: {e}")
            return {'deleted': 0}