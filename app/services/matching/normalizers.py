"""
Name and address normalizers for matching.
"""

import re
import unicodedata


def normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    if not name:
        return ''
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove diacritics
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    
    # Remove common suffixes
    suffixes = [
        'gesellschaft mit beschränkter haftung',
        'gesellschaft mit',
        'aktiengesellschaft',
        'kommanditgesellschaft',
        'haftung',
        'gmbh',
        'kg',
        'ag',
        'ohg',
        'ug',
        'se',
        'co',
        'partner',
    ]
    
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    
    # Remove non-alphanumeric
    name = re.sub(r'[^a-z0-9]', '', name)
    
    return name


def normalize_address(address: str) -> str:
    """Normalize address for matching."""
    if not address:
        return ''
    
    # Convert to lowercase
    address = address.lower()
    
    # Remove diacritics
    address = unicodedata.normalize('NFD', address)
    address = ''.join(c for c in address if unicodedata.category(c) != 'Mn')
    
    # Normalize street types
    street_types = {
        r'\bstr\.?\b': 'straße',
        r'\bstrasse\b': 'straße',
        r'\bplatz\b': 'platz',
        r'\bweg\b': 'weg',
        r'\b allee\b': 'allee',
    }
    
    for pattern, replacement in street_types.items():
        address = re.sub(pattern, replacement, address)
    
    # Remove non-alphanumeric
    address = re.sub(r'[^a-z0-9]', '', address)
    
    return address


def normalize_postal_code(code: str) -> str:
    """Normalize postal code."""
    if not code:
        return ''
    
    # Remove spaces and non-digits
    code = re.sub(r'[^0-9]', '', code)
    
    return code


def normalize_city(city: str) -> str:
    """Normalize city name."""
    if not city:
        return ''
    
    # Convert to lowercase
    city = city.lower()
    
    # Remove diacritics
    city = unicodedata.normalize('NFD', city)
    city = ''.join(c for c in city if unicodedata.category(c) != 'Mn')
    
    # Remove common additions
    removals = [' (klein)', ' (groß)', '-mittel', '-ober', '-unter']
    
    for removal in removals:
        city = city.replace(removal, '')
    
    # Remove non-alphanumeric except space
    city = re.sub(r'[^a-zäöüß ]', '', city)
    
    return city.strip()