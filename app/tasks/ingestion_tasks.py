"""
Celery Ingestion Tasks

Background tasks for data ingestion from various sources.
"""

import logging
import uuid
from datetime import datetime
from celery import shared_task


logger = logging.getLogger('company_intel.tasks.ingestion')


def get_app():
    """Get Flask app instance for Celery context."""
    from app import create_app
    from app.core.config import get_config
    return create_app(get_config())


def get_source_connector(source_name: str):
    """Get the appropriate connector for a source."""
    connectors = {
        'offeneregister': 'app.sources.offeneregister.OffeneRegisterConnector',
        'opencorporates': 'app.sources.opencorporates.OpenCorporatesConnector',
        'gleif': 'app.sources.gleif.GLEIFConnector',
        'openownership': 'app.sources.openownership.OpenOwnershipConnector',
        'opensanctions': 'app.sources.opensanctions.OpenSanctionsConnector',
        'openlegaldata': 'app.sources.openlegaldata.OpenLegalDataConnector',
        'govdata': 'app.sources.govdata.GovDataConnector',
        'osm': 'app.sources.osm.OSMConnector',
    }
    
    if source_name not in connectors:
        raise ValueError(f"Unknown source: {source_name}")
    
    # Dynamic import
    module_path, class_name = connectors[source_name].rsplit('.', 1)
    import importlib
    module = importlib.import_module(module_path)
    connector_class = getattr(module, class_name)
    
    return connector_class()


@shared_task(bind=True, max_retries=3)
def run_ingestion(self, source_name: str, full: bool = False):
    """Run full or incremental ingestion for a source."""
    from app.models import IngestionJob, SourceSyncState
    from app.core.extensions import db
    
    job_id = str(uuid.uuid4())
    app = get_app()
    
    with app.app_context():
        job = IngestionJob(
            job_id=job_id,
            job_type='FULL_INGEST' if full else 'INCREMENTAL_SYNC',
            source=source_name,
            status='running',
            started_at=datetime.utcnow(),
        )
        db.session.add(job)
        db.session.commit()
        
        logger.info(f"Starting ingestion job {job_id} for {source_name}")
        
        processed = 0
        failed = 0
        
        try:
            connector = get_source_connector(source_name)
            
            # Fetch records
            for record in connector.fetch_all():
                try:
                    connector.save_record(record)
                    processed += 1
                    
                    # Update job progress periodically
                    if processed % 100 == 0:
                        job.processed_items = processed
                        db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to process record: {e}")
                    failed += 1
            
            # Complete job
            job.status = 'completed'
            job.processed_items = processed
            job.failed_items = failed
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Ingestion job {job_id} completed: {processed} processed, {failed} failed")
            
        except Exception as e:
            logger.error(f"Ingestion job {job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            raise self.retry(exc=e, countdown=60)
    
    return {'job_id': job_id, 'processed': processed, 'failed': failed}


@shared_task(bind=True, max_retries=3)
def run_matching(self):
    """Run entity matching on all companies."""
    from app.services.matching import MatchingService
    from app.models import IngestionJob
    from app.core.extensions import db
    
    job_id = str(uuid.uuid4())
    app = get_app()
    
    with app.app_context():
        job = IngestionJob(
            job_id=job_id,
            job_type='MATCH',
            status='running',
            started_at=datetime.utcnow(),
        )
        db.session.add(job)
        db.session.commit()
        
        logger.info(f"Starting matching job {job_id}")
        
        matches = 0
        
        try:
            matching_service = MatchingService()
            matches = matching_service.match_all_companies()
            
            job.status = 'completed'
            job.processed_items = matches
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Matching job {job_id} completed: {matches} matches")
            
        except Exception as e:
            logger.error(f"Matching job {job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            raise self.retry(exc=e, countdown=60)
    
    return {'job_id': job_id, 'matches': matches}


@shared_task(bind=True, max_retries=3)
def run_screening(self, company_id: int = None):
    """Run sanctions screening."""
    from app.services.screening import ScreeningService
    from app.models import IngestionJob
    from app.core.extensions import db
    
    job_id = str(uuid.uuid4())
    app = get_app()
    
    with app.app_context():
        job = IngestionJob(
            job_id=job_id,
            job_type='SCREENING',
            status='running',
            started_at=datetime.utcnow(),
        )
        db.session.add(job)
        db.session.commit()
        
        logger.info(f"Starting screening job {job_id}")
        
        hits = 0
        
        try:
            screening_service = ScreeningService()
            hits = screening_service.screen_company(company_id) if company_id else screening_service.screen_all()
            
            job.status = 'completed'
            job.processed_items = hits
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Screening job {job_id} completed: {hits} hits")
            
        except Exception as e:
            logger.error(f"Screening job {job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            raise self.retry(exc=e, countdown=60)
    
    return {'job_id': job_id, 'hits': hits}


@shared_task(bind=True, max_retries=3)
def run_discovery(self):
    """Run dataset discovery."""
    from app.services.discovery import DatasetDiscoveryService
    from app.models import IngestionJob
    from app.core.extensions import db
    
    job_id = str(uuid.uuid4())
    app = get_app()
    
    with app.app_context():
        job = IngestionJob(
            job_id=job_id,
            job_type='DISCOVERY',
            status='running',
            started_at=datetime.utcnow(),
        )
        db.session.add(job)
        db.session.commit()
        
        logger.info(f"Starting discovery job {job_id}")
        
        discovered = 0
        
        try:
            discovery_service = DatasetDiscoveryService()
            discovered = discovery_service.discover_all()
            
            job.status = 'completed'
            job.processed_items = discovered
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Discovery job {job_id} completed: {discovered} datasets")
            
        except Exception as e:
            logger.error(f"Discovery job {job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            raise self.retry(exc=e, countdown=60)
    
    return {'job_id': job_id, 'discovered': discovered}