#!/usr/bin/env python3
"""
Student Performance Prediction and Learning Management System
Main application entry point
"""

import os
from app import create_app, db
from app.models import User, Course, Assignment, Enrollment, Submission, Grade

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Course': Course,
        'Assignment': Assignment,
        'Enrollment': Enrollment,
        'Submission': Submission,
        'Grade': Grade
    }

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )