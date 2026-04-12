from flask import Blueprint, send_from_directory
import os

main = Blueprint('main', __name__)

DIST = os.path.join(os.path.dirname(__file__), '..', 'static', 'dist')

@main.route('/', defaults={'path': ''})
@main.route('/<path:path>')
def index(path):
    # Serve static assets directly; fall back to index.html for SPA routing
    file_path = os.path.join(DIST, path)
    if path and os.path.isfile(file_path):
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, 'index.html')
