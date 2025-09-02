import pytest
import json
from app import create_app, db
from app.models import User, UserRole

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_student_success(self, client):
        """Test successful student registration."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'student',
            'roll_number': 'STU001'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['message'] == 'User registered successfully'
        assert result['user']['email'] == 'john.doe@example.com'
        assert result['user']['role'] == 'student'
    
    def test_register_teacher_success(self, client):
        """Test successful teacher registration."""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'teacher'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['message'] == 'User registered successfully'
        assert result['user']['role'] == 'teacher'
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        data = {
            'first_name': 'John',
            'email': 'john@example.com'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_register_password_mismatch(self, client):
        """Test registration with password mismatch."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'confirm_password': 'different',
            'role': 'student',
            'roll_number': 'STU001'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'Passwords do not match'
    
    def test_register_invalid_role(self, client):
        """Test registration with invalid role."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'invalid'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'Invalid role' in result['error']
    
    def test_register_student_missing_roll_number(self, client):
        """Test student registration without roll number."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'student'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'Roll number is required for students'
    
    def test_login_success(self, client, app):
        """Test successful login."""
        # First register a user
        with app.app_context():
            user = User(
                first_name='John',
                last_name='Doe',
                email='john@example.com',
                role=UserRole.STUDENT,
                roll_number='STU001'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        data = {
            'email': 'john@example.com',
            'password': 'password123',
            'role': 'student'
        }
        
        response = client.post('/api/auth/login', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['message'] == 'Login successful'
        assert result['user']['email'] == 'john@example.com'
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword',
            'role': 'student'
        }
        
        response = client.post('/api/auth/login', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        result = json.loads(response.data)
        assert result['error'] == 'Invalid email or password'
    
    def test_login_role_mismatch(self, client, app):
        """Test login with role mismatch."""
        # Register a teacher
        with app.app_context():
            user = User(
                first_name='Jane',
                last_name='Smith',
                email='jane@example.com',
                role=UserRole.TEACHER
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Try to login as student
        data = {
            'email': 'jane@example.com',
            'password': 'password123',
            'role': 'student'
        }
        
        response = client.post('/api/auth/login', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        result = json.loads(response.data)
        assert result['error'] == 'Invalid role for this user'