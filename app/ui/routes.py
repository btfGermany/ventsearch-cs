"""
Web UI Routes
"""

from flask import Blueprint, send_from_directory
import os


ui_bp = Blueprint('ui', __name__)

# Get static folder path
STATIC_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    'static'
)


@ui_bp.route('/')
def index():
    """Serve the main UI page."""
    return send_from_directory(STATIC_PATH, 'index.html')


@ui_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory(STATIC_PATH, filename)