#!/usr/bin/env python3
"""
Simple demo Flask app to show the structure works
Run without dependencies for demonstration
"""

from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import hashlib
import json
from datetime import datetime

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['SECRET_KEY'] = 'demo-secret-key'

# Database initialization
def init_db():
    conn = sqlite3.connect('demo.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'teacher')),
            roll_number TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            description TEXT,
            teacher_id INTEGER,
            credits INTEGER DEFAULT 3,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash_value):
    return hashlib.sha256(password.encode()).hexdigest() == hash_value

# Routes
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        if data['password'] != data['confirm_password']:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        if data['role'] not in ['student', 'teacher']:
            return jsonify({'error': 'Invalid role'}), 400
        
        if data['role'] == 'student' and not data.get('roll_number'):
            return jsonify({'error': 'Roll number is required for students'}), 400
        
        # Check if email exists
        conn = sqlite3.connect('demo.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Insert user
        password_hash = hash_password(data['password'])
        cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, role, roll_number)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['email'], password_hash, data['first_name'], data['last_name'], 
              data['role'], data.get('roll_number')))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user_id,
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': data['role'],
                'roll_number': data.get('roll_number')
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password') or not data.get('role'):
            return jsonify({'error': 'Email, password, and role are required'}), 400
        
        conn = sqlite3.connect('demo.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, password_hash, first_name, last_name, role, roll_number 
            FROM users WHERE email = ? AND role = ?
        ''', (data['email'], data['role']))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(data['password'], user[2]):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user[0],
                'email': user[1],
                'first_name': user[3],
                'last_name': user[4],
                'role': user[5],
                'roll_number': user[6]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/dashboard/student', methods=['GET'])
def student_dashboard():
    return jsonify({
        'courses': [
            {'id': 1, 'name': 'Introduction to Programming', 'code': 'CS101', 'teacher_name': 'Dr. Smith', 'credits': 3},
            {'id': 2, 'name': 'Data Structures', 'code': 'CS201', 'teacher_name': 'Prof. Johnson', 'credits': 4}
        ],
        'recent_assignments': [
            {'id': 1, 'title': 'Python Basics', 'course_name': 'CS101', 'due_date': '2024-01-15', 'max_score': 100},
            {'id': 2, 'title': 'Linked Lists', 'course_name': 'CS201', 'due_date': '2024-01-20', 'max_score': 50}
        ],
        'grades': [
            {'id': 1, 'score': 85, 'assignment_id': 1},
            {'id': 2, 'score': 92, 'assignment_id': 2}
        ],
        'stats': {
            'total_courses': 2,
            'total_assignments': 5,
            'submitted_assignments': 3,
            'average_grade': 88.5
        }
    })

@app.route('/api/dashboard/teacher', methods=['GET'])
def teacher_dashboard():
    return jsonify({
        'courses': [
            {'id': 1, 'name': 'Introduction to Programming', 'code': 'CS101', 'description': 'Basic programming concepts', 'credits': 3},
            {'id': 2, 'name': 'Advanced Programming', 'code': 'CS301', 'description': 'Advanced topics', 'credits': 4}
        ],
        'assignments': [
            {'id': 1, 'title': 'Python Basics', 'course_name': 'CS101', 'due_date': '2024-01-15', 'max_score': 100},
            {'id': 2, 'title': 'Object-Oriented Programming', 'course_name': 'CS301', 'due_date': '2024-01-25', 'max_score': 150}
        ],
        'stats': {
            'total_courses': 2,
            'total_students': 45,
            'total_assignments': 8,
            'total_submissions': 67,
            'graded_submissions': 45
        }
    })

@app.route('/api/ml/predict/<int:student_id>', methods=['GET'])
def predict_performance(student_id):
    # Demo prediction data
    return jsonify({
        'student_id': student_id,
        'insights': {
            'prediction': {
                'predicted_performance': 87.5,
                'current_performance': 85.0,
                'feature_importance': {
                    'consistency': 0.3,
                    'improvement_trend': 0.4,
                    'assignment_completion': 0.3
                }
            },
            'insights': [
                {
                    'type': 'positive',
                    'message': 'Your performance is improving! Predicted: 87.5%'
                }
            ],
            'recommendations': [
                'Keep up the excellent work!',
                'Focus on consistency in submissions',
                'Consider helping other students'
            ]
        }
    })

@app.route('/api/ml/train', methods=['POST'])
def train_model():
    return jsonify({'message': 'Model training completed successfully (demo version)'}), 200

if __name__ == '__main__':
    init_db()
    print("Starting Student Management System Demo...")
    print("Visit http://localhost:5000 to access the application")
    app.run(host='0.0.0.0', port=5000, debug=True)