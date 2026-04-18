"""
Matching service module exports.
"""

from app.services.matching.matching_service import MatchingService
from app.services.matching.normalizers import normalize_name, normalize_address

__all__ = ['MatchingService', 'normalize_name', 'normalize_address']