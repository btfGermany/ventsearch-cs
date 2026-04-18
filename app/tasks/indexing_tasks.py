"""
Celery Indexing Tasks

Background tasks for indexing data to OpenSearch.
"""

import logging
from celery import shared_task
from app.core.extensions import db


logger = logging.getLogger('company_intel.tasks.indexing')


@shared_task(bind=True)
def run_reindex(self):
    """Reindex all companies to OpenSearch."""
    from app.models import Company
    from app.services.search import SearchService
    from flask import current_app
    
    logger.info("Starting reindex job")
    
    indexed = 0
    
    with current_app.app_context():
        search_service = None
        
        if hasattr(current_app, 'opensearch'):
            search_service = current_app.opensearch.get_service()
        
        if not search_service or not search_service.is_available:
            logger.warning("OpenSearch not available, skipping reindex")
            return {'indexed': 0}
        
        # Get all unmerged companies
        companies = Company.query.filter_by(is_merged=False).all()
        
        for company in companies:
            try:
                doc = company.to_dict()
                if search_service.index_company(doc):
                    indexed += 1
            except Exception as e:
                logger.error(f"Failed to index company {company.id}: {e}")
        
        logger.info(f"Reindex complete: {indexed} companies indexed")
    
    return {'indexed': indexed}


@shared_task
def index_company(company_id: int):
    """Index a single company."""
    from app.models import Company
    from app.services.search import SearchService
    from flask import current_app
    
    with current_app.app_context():
        search_service = None
        
        if hasattr(current_app, 'opensearch'):
            search_service = current_app.opensearch.get_service()
        
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
    from flask import current_app
    
    with current_app.app_context():
        search_service = None
        
        if hasattr(current_app, 'opensearch'):
            search_service = current_app.opensearch.get_service()
        
        if not search_service or not search_service.is_available:
            return {'deleted': 0}
        
        try:
            success = search_service.delete_company(company_id)
            return {'deleted': 1 if success else 0}
        except Exception as e:
            logger.error(f"Failed to delete company {company_id}: {e}")
            return {'deleted': 0}