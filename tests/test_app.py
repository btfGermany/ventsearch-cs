"""
Tests for Company Intelligence Aggregator Platform.
"""

import pytest
from app import create_app
from app.core.extensions import db


@pytest.fixture
def app():
    """Create application for testing."""
    from app.core.config import TestingConfig
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


class TestHealth:
    """Test health endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint returns healthy."""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_ping(self, client):
        """Test ping endpoint."""
        response = client.get('/api/v1/ping')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['pong'] is True


class TestCompanies:
    """Test companies endpoint."""
    
    def test_list_companies_empty(self, client):
        """Test listing companies when empty."""
        response = client.get('/api/v1/companies')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['total'] == 0
        assert data['companies'] == []
    
    def test_get_company_not_found(self, client):
        """Test getting non-existent company."""
        response = client.get('/api/v1/companies/99999')
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'error' in data


class TestSources:
    """Test sources endpoint."""
    
    def test_list_sources(self, client):
        """Test listing sources."""
        response = client.get('/api/v1/sources')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'sources' in data


class TestMatching:
    """Test matching service."""
    
    def test_name_normalization(self):
        """Test name normalization."""
        from app.services.matching.normalizers import normalize_name
        
        # Test basic normalization
        assert normalize_name('Test GmbH') == 'test'
        assert normalize_name('Test AG') == 'test'
        
        # Test with umlauts
        assert normalize_name('Müller') == 'muller'
    
    def test_string_similarity(self):
        """Test string similarity."""
        from app.services.matching import MatchingService
        
        service = MatchingService()
        
        # Same string
        assert service._string_similarity('test', 'test') == 1.0
        
        # Different strings
        similarity = service._string_similarity('test', 'testing')
        assert 0 < similarity < 1


class TestScreening:
    """Test screening service."""
    
    def test_screening_service_init(self):
        """Test screening service initialization."""
        from app.services.screening import ScreeningService
        
        service = ScreeningService()
        assert service is not None


class TestSearch:
    """Test search service."""
    
    def test_search_service_init(self):
        """Test search service initialization."""
        from app.services.search import SearchService
        
        service = SearchService()
        assert service is not None
    
    def test_search_service_not_available(self):
        """Test search when OpenSearch not available."""
        from app.services.search import SearchService
        
        service = SearchService()
        
        # Without client, service should not be available
        results = service.search('test')
        
        assert results['total'] == 0


class TestModels:
    """Test model functionality."""
    
    def test_company_to_dict(self, app):
        """Test company to_dict."""
        from app.models import Company
        
        with app.app_context():
            company = Company(
                uuid='test-uuid',
                canonical_name='Test GmbH',
                country='DE',
            )
            
            data = company.to_dict()
            
            assert data['uuid'] == 'test-uuid'
            assert data['canonical_name'] == 'Test GmbH'
    
    def test_company_name_to_dict(self, app):
        """Test company name to_dict."""
        from app.models import CompanyName
        
        with app.app_context():
            name = CompanyName(
                name='Test GmbH',
                name_type='legal_name',
                source='test',
            )
            
            data = name.to_dict()
            
            assert data['name'] == 'Test GmbH'
            assert data['name_type'] == 'legal_name'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])