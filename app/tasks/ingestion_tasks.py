"""
Celery Ingestion Tasks

Background tasks for data ingestion from various sources.
"""

import logging
import uuid
from datetime import datetime
from celery import shared_task
from app.core.extensions import db


logger = logging.getLogger('company_intel.tasks.ingestion')


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
    from flask import current_app
    
    job_id = str(uuid.uuid4())
    
    # Log to database
    with current_app.app_context():
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
        
        try:
            connector = get_source_connector(source_name)
            processed = 0
            failed = 0
            
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
            
            # Mark job complete
            job.status = 'completed'
            job.processed_items = processed
            job.failed_items = failed
            job.completed_at = datetime.utcnow()
            job.results = {'processed': processed, 'failed': failed}
            
            # Update sync state
            sync_state = SourceSyncState.query.filter_by(source=source_name).first()
            if sync_state:
                sync_state.last_sync_at = datetime.utcnow()
                sync_state.total_synced += processed
                sync_state.total_failed += failed
                sync_state.sync_status = 'idle'
            else:
                sync_state = SourceSyncState(
                    source=source_name,
                    last_sync_at=datetime.utcnow(),
                    total_synced=processed,
                    total_failed=failed,
                    sync_status='idle',
                )
                db.session.add(sync_state)
            
            db.session.commit()
            
            logger.info(f"Completed ingestion job {job_id}: {processed} processed, {failed} failed")
            
        except Exception as e:
            logger.error(f"Ingestion job failed: {e}")
            
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Retry
            raise self.retry(exc=e, countdown=60)
    
    return {'job_id': job_id, 'processed': processed, 'failed': failed}


@shared_task
def run_matching():
    """Run entity resolution matching for all companies."""
    from app.models import Company
    from app.services.matching import MatchingService
    
    logger.info("Starting matching job")
    
    with db.app.app_context():
        companies = Company.query.filter_by(is_merged=False).all()
        service = MatchingService()
        
        matches_found = 0
        
        for company in companies:
            matches = service.find_matches(company)
            auto_merge = [m for m in matches if m.get('should_merge')]
            
            for match in auto_merge[:1]:  # Only process best match
                target = db.session.get(Company, match['company_id'])
                if target:
                    service.merge_companies(company, target)
                    matches_found += 1
        
        logger.info(f"Matching complete: {matches_found} merges")
    
    return {'matches_found': matches_found}


@shared_task
def run_screening():
    """Run sanctions screening for all companies."""
    from app.models import Company
    from app.services.screening import ScreeningService
    
    logger.info("Starting screening job")
    
    screened = 0
    matches_found = 0
    
    with db.app.app_context():
        companies = Company.query.filter_by(is_merged=False).all()
        service = ScreeningService()
        
        for company in companies:
            results = service.screen_company(company)
            if results:
                for result in results:
                    entity_id = result['sanctions_entity_id']
                    from app.models import SanctionsEntity
                    entity = db.session.get(SanctionsEntity, entity_id)
                    if entity:
                        service.create_match_record(
                            company=company,
                            entity=entity,
                            match_type=result['match_type'],
                            match_score=result['match_score'],
                            matched_field=result['matched_field'],
                            matched_value=result['matched_value'],
                        )
                        matches_found += 1
            screened += 1
        
        logger.info(f"Screening complete: {screened} screened, {matches_found} matches")
    
    return {'screened': screened, 'matches_found': matches_found}


@shared_task
def run_discovery():
    """Run dataset discovery crawler."""
    from app.services.discovery.crawler import DiscoveryCrawler
    
    logger.info("Starting discovery crawl")
    
    count = 0
    
    with db.app.app_context():
        crawler = DiscoveryCrawler()
        count = crawler.crawl()
        
        logger.info(f"Discovery complete: {count} datasets")
    
    return {'datasets_found': count}