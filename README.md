# Student Performance Prediction and Learning Management System

A complete full-stack learning management system with intelligent student performance prediction using machine learning.

## Features

### Backend Features
- **Flask Application**: RESTful API with SQLAlchemy ORM
- **JWT Authentication**: Secure role-based access control (Student/Teacher)
- **Database**: MariaDB/MySQL support with proper relationships
- **Machine Learning**: Student performance prediction with insights
- **Email Integration**: Notification system
- **Rate Limiting**: API protection and security
- **Background Tasks**: Celery integration for async processing

### Frontend Features
- **Responsive Design**: Tailwind CSS for mobile and desktop
- **Interactive Dashboards**: Role-specific interfaces
- **Real-time Charts**: Chart.js visualizations
- **Form Validation**: Client-side and server-side validation
- **Authentication Flow**: Login/signup with role selection

### Core Functionality
- **Course Management**: Create and manage courses
- **Assignment System**: Create, submit, and grade assignments
- **Student Enrollment**: Course registration system
- **Grade Management**: Comprehensive grading system
- **Performance Analytics**: ML-powered insights and predictions
- **Role-based Access**: Separate interfaces for students and teachers

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-JWT-Extended, Flask-Mail
- **Database**: MariaDB/MySQL with PyMySQL connector
- **Frontend**: HTML5, Tailwind CSS, Chart.js, Vanilla JavaScript
- **Machine Learning**: scikit-learn, pandas, numpy
- **Authentication**: JWT with HttpOnly cookies
- **Task Queue**: Celery with Redis
- **Development**: Flask development server, npm scripts

## Project Structure

```
student-performance-system/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration management
│   ├── models/               # Database models
│   ├── auth/                 # Authentication routes
│   ├── api/                  # API endpoints
│   ├── ml/                   # Machine learning pipeline
│   └── utils/                # Utility functions
├── migrations/               # Database migrations
├── public/                   # Frontend static files
│   ├── login.html           # Login page
│   ├── signup.html          # Registration page
│   ├── dashboard_student.html # Student dashboard
│   ├── dashboard_teacher.html # Teacher dashboard
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript utilities
│   └── config.js            # Frontend configuration (generated)
├── scripts/
│   └── generateConfig.js    # Config generation script
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── package.json             # Node.js dependencies
├── tailwind.config.js       # Tailwind configuration
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- MariaDB/MySQL
- Redis (optional, for background tasks)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd student-performance-system
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Required Environment Variables
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/database_name
JWT_SECRET=your-jwt-secret-here
JWT_ACCESS_EXPIRES=900
JWT_REFRESH_EXPIRES=1209600
MODEL_DIR=./models
MODEL_VERSION=v0.0.0
SENTRY_DSN=
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
FRONTEND_API_URL=http://localhost:5000/api
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup
```bash
# Create database in MariaDB/MySQL
mysql -u root -p
CREATE DATABASE student_management;
CREATE USER 'sms_user'@'localhost' IDENTIFIED BY 'strongpass';
GRANT ALL PRIVILEGES ON student_management.* TO 'sms_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Frontend Setup
```bash
# Install Node.js dependencies
npm install

# Build frontend assets
npm run build
```

### 6. Run the Application
```bash
# Start the Flask development server
python app.py

# Or use Flask command
flask run
```

The application will be available at `http://localhost:5000`

## API Documentation

### Authentication Endpoints

#### POST /api/auth/register
Register a new user (student or teacher)

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "password": "securepassword",
  "confirm_password": "securepassword",
  "role": "student",
  "roll_number": "STU001"
}
```

#### POST /api/auth/login
Login user

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "password": "securepassword",
  "role": "student"
}
```

#### POST /api/auth/logout
Logout user (clears JWT cookies)

#### POST /api/auth/refresh
Refresh JWT access token

#### GET /api/auth/me
Get current user information

### Course Endpoints

#### GET /api/courses
Get courses (filtered by user role)

#### POST /api/courses
Create new course (teachers only)

#### GET /api/courses/{id}
Get specific course details

### Assignment Endpoints

#### GET /api/assignments
Get assignments (with optional course filter)

#### POST /api/assignments
Create new assignment (teachers only)

### Submission Endpoints

#### GET /api/submissions
Get submissions (filtered by user role)

#### POST /api/submissions
Submit assignment (students only)

### Grade Endpoints

#### GET /api/grades
Get grades (filtered by user role)

#### POST /api/grades
Create grade (teachers only)

### Machine Learning Endpoints

#### GET /api/ml/predict/{student_id}
Get performance prediction and insights for student

#### POST /api/ml/train
Train ML model (teachers only)

### Dashboard Endpoints

#### GET /api/dashboard/student
Get student dashboard data

#### GET /api/dashboard/teacher
Get teacher dashboard data

## Database Schema

### Users Table
- `id` (Primary Key)
- `email` (Unique)
- `password_hash`
- `first_name`
- `last_name`
- `role` (student/teacher)
- `roll_number` (students only)
- `is_active`
- `created_at`
- `updated_at`

### Courses Table
- `id` (Primary Key)
- `name`
- `code` (Unique)
- `description`
- `teacher_id` (Foreign Key → Users)
- `credits`
- `is_active`
- `created_at`
- `updated_at`

### Enrollments Table
- `id` (Primary Key)
- `student_id` (Foreign Key → Users)
- `course_id` (Foreign Key → Courses)
- `enrolled_at`
- `is_active`

### Assignments Table
- `id` (Primary Key)
- `title`
- `description`
- `course_id` (Foreign Key → Courses)
- `max_score`
- `due_date`
- `is_active`
- `created_at`
- `updated_at`

### Submissions Table
- `id` (Primary Key)
- `assignment_id` (Foreign Key → Assignments)
- `student_id` (Foreign Key → Users)
- `content`
- `file_path`
- `submitted_at`
- `is_late`

### Grades Table
- `id` (Primary Key)
- `assignment_id` (Foreign Key → Assignments)
- `student_id` (Foreign Key → Users)
- `score`
- `feedback`
- `graded_at`
- `graded_by` (Foreign Key → Users)

## Machine Learning Pipeline

### Features Used
- Average performance percentage
- Performance standard deviation
- Performance trend (improvement/decline)
- Total assignments completed
- Performance range (max - min)
- Course load metrics

### Model Details
- **Algorithm**: Random Forest Regressor
- **Features**: Engineered from student performance data
- **Target**: Future performance prediction
- **Evaluation**: MSE and R² score

### Training Process
1. Extract features from student grades
2. Engineer additional features (trends, statistics)
3. Split data for training/testing
4. Train Random Forest model
5. Evaluate performance
6. Save model for predictions

## Development Workflow

### Running in Development Mode
```bash
# Backend development
export FLASK_ENV=development
python app.py

# Frontend development (watch mode)
npm run dev
```

### Testing
```bash
# Run Python tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/
```

### Database Migrations
```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade (if needed)
flask db downgrade
```

### Frontend Build
```bash
# Build CSS
npm run build:css

# Generate config
npm run build:config

# Build all
npm run build
```

## Security Features

### Authentication Security
- JWT tokens with HttpOnly cookies
- CSRF protection enabled
- Secure cookie configuration
- Token refresh mechanism
- Rate limiting on auth endpoints

### API Security
- Role-based access control
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection

### Password Security
- bcrypt hashing
- Minimum length requirements
- Password confirmation

## Deployment

### Production Configuration
1. Set `FLASK_ENV=production`
2. Use strong secret keys
3. Configure proper database
4. Set up reverse proxy (nginx)
5. Enable HTTPS
6. Configure monitoring (Sentry)

### Environment Variables for Production
```env
FLASK_ENV=production
SECRET_KEY=very-strong-production-secret
DATABASE_URL=mysql+pymysql://user:pass@prod-db:3306/db
JWT_SECRET=strong-jwt-secret
SENTRY_DSN=your-sentry-dsn
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API endpoints

## Changelog

### Version 1.0.0
- Initial release
- Complete authentication system
- Course and assignment management
- Machine learning predictions
- Responsive frontend interfaces
- Comprehensive API documentation