# Test configuration
import tempfile
import os

# Test database (in-memory SQLite)
DATABASE_URL = 'sqlite:///:memory:'

# Disable CSRF for testing
WTF_CSRF_ENABLED = False

# Use a temporary directory for file uploads during testing
UPLOAD_FOLDER = tempfile.gettempdir()

# Testing secret key
SECRET_KEY = 'test-secret-key'
JWT_SECRET_KEY = 'test-jwt-secret'