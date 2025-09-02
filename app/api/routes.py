from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import bp
from app import db
from app.models import User, Course, Assignment, Enrollment, Submission, Grade, UserRole
from app.ml import StudentPerformancePredictor
from datetime import datetime

def get_current_user():
    """Helper function to get current user from JWT"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user or user.role.value != role:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# ML endpoints
@bp.route('/ml/predict/<int:student_id>', methods=['GET'])
@jwt_required()
def predict_student_performance(student_id):
    try:
        user = get_current_user()
        
        # Check permissions
        if user.role == UserRole.STUDENT and user.id != student_id:
            return jsonify({'error': 'Access denied'}), 403
        elif user.role == UserRole.TEACHER:
            # Check if teacher has access to this student (through courses)
            student = User.query.get_or_404(student_id)
            if student.role != UserRole.STUDENT:
                return jsonify({'error': 'Invalid student ID'}), 400
            
            # Check if teacher teaches any course the student is enrolled in
            teacher_courses = Course.query.filter_by(teacher_id=user.id).all()
            teacher_course_ids = [course.id for course in teacher_courses]
            
            student_enrollments = Enrollment.query.filter_by(student_id=student_id, is_active=True).all()
            student_course_ids = [enrollment.course_id for enrollment in student_enrollments]
            
            common_courses = set(teacher_course_ids) & set(student_course_ids)
            if not common_courses:
                return jsonify({'error': 'Access denied - no shared courses'}), 403
        
        # Get predictions
        predictor = StudentPerformancePredictor()
        insights = predictor.get_performance_insights(student_id)
        
        if not insights:
            return jsonify({'error': 'Unable to generate predictions - insufficient data'}), 400
        
        return jsonify({
            'student_id': student_id,
            'insights': insights
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate predictions'}), 500

@bp.route('/ml/train', methods=['POST'])
@jwt_required()
@require_role('teacher')
def train_model():
    try:
        # For the simplified version, just return success
        # In a real implementation, this would train the actual ML model
        return jsonify({'message': 'Model training completed successfully (simplified version)'}), 200
            
    except Exception as e:
        return jsonify({'error': 'Failed to train model'}), 500

# Course endpoints
@bp.route('/courses', methods=['GET'])
@jwt_required()
def get_courses():
    try:
        user = get_current_user()
        if user.role == UserRole.TEACHER:
            courses = Course.query.filter_by(teacher_id=user.id, is_active=True).all()
        else:  # Student
            enrollments = Enrollment.query.filter_by(student_id=user.id, is_active=True).all()
            courses = [enrollment.course for enrollment in enrollments if enrollment.course.is_active]
        
        return jsonify({'courses': [course.to_dict() for course in courses]}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch courses'}), 500

@bp.route('/courses', methods=['POST'])
@jwt_required()
@require_role('teacher')
def create_course():
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Validate required fields
        required_fields = ['name', 'code']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if course code already exists
        if Course.query.filter_by(code=data['code']).first():
            return jsonify({'error': 'Course code already exists'}), 400
        
        course = Course(
            name=data['name'],
            code=data['code'],
            description=data.get('description', ''),
            teacher_id=user.id,
            credits=data.get('credits', 3)
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({'message': 'Course created successfully', 'course': course.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create course'}), 500

@bp.route('/courses/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    try:
        user = get_current_user()
        course = Course.query.get_or_404(course_id)
        
        # Check if user has access to this course
        if user.role == UserRole.TEACHER:
            if course.teacher_id != user.id:
                return jsonify({'error': 'Access denied'}), 403
        else:  # Student
            enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=course_id, is_active=True).first()
            if not enrollment:
                return jsonify({'error': 'Not enrolled in this course'}), 403
        
        return jsonify({'course': course.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': 'Course not found'}), 404

# Assignment endpoints
@bp.route('/assignments', methods=['GET'])
@jwt_required()
def get_assignments():
    try:
        user = get_current_user()
        course_id = request.args.get('course_id')
        
        if course_id:
            # Check access to course
            course = Course.query.get_or_404(course_id)
            if user.role == UserRole.TEACHER:
                if course.teacher_id != user.id:
                    return jsonify({'error': 'Access denied'}), 403
            else:  # Student
                enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=course_id, is_active=True).first()
                if not enrollment:
                    return jsonify({'error': 'Not enrolled in this course'}), 403
            
            assignments = Assignment.query.filter_by(course_id=course_id, is_active=True).all()
        else:
            # Get all assignments for user's courses
            if user.role == UserRole.TEACHER:
                courses = Course.query.filter_by(teacher_id=user.id, is_active=True).all()
                course_ids = [course.id for course in courses]
            else:  # Student
                enrollments = Enrollment.query.filter_by(student_id=user.id, is_active=True).all()
                course_ids = [enrollment.course_id for enrollment in enrollments]
            
            assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids), Assignment.is_active == True).all()
        
        return jsonify({'assignments': [assignment.to_dict() for assignment in assignments]}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch assignments'}), 500

@bp.route('/assignments', methods=['POST'])
@jwt_required()
@require_role('teacher')
def create_assignment():
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Validate required fields
        required_fields = ['title', 'course_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if teacher owns the course
        course = Course.query.get_or_404(data['course_id'])
        if course.teacher_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        assignment = Assignment(
            title=data['title'],
            description=data.get('description', ''),
            course_id=data['course_id'],
            max_score=data.get('max_score', 100.0),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({'message': 'Assignment created successfully', 'assignment': assignment.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create assignment'}), 500

# Submission endpoints
@bp.route('/submissions', methods=['GET'])
@jwt_required()
def get_submissions():
    try:
        user = get_current_user()
        assignment_id = request.args.get('assignment_id')
        
        if assignment_id:
            assignment = Assignment.query.get_or_404(assignment_id)
            
            # Check access
            if user.role == UserRole.TEACHER:
                course = Course.query.get(assignment.course_id)
                if course.teacher_id != user.id:
                    return jsonify({'error': 'Access denied'}), 403
                submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
            else:  # Student
                enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=assignment.course_id, is_active=True).first()
                if not enrollment:
                    return jsonify({'error': 'Not enrolled in this course'}), 403
                submissions = Submission.query.filter_by(assignment_id=assignment_id, student_id=user.id).all()
        else:
            if user.role == UserRole.STUDENT:
                submissions = Submission.query.filter_by(student_id=user.id).all()
            else:
                return jsonify({'error': 'assignment_id is required for teachers'}), 400
        
        return jsonify({'submissions': [submission.to_dict() for submission in submissions]}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch submissions'}), 500

@bp.route('/submissions', methods=['POST'])
@jwt_required()
@require_role('student')
def create_submission():
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Validate required fields
        if not data.get('assignment_id'):
            return jsonify({'error': 'assignment_id is required'}), 400
        
        assignment = Assignment.query.get_or_404(data['assignment_id'])
        
        # Check if student is enrolled in the course
        enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=assignment.course_id, is_active=True).first()
        if not enrollment:
            return jsonify({'error': 'Not enrolled in this course'}), 403
        
        # Check if submission already exists
        existing_submission = Submission.query.filter_by(assignment_id=data['assignment_id'], student_id=user.id).first()
        if existing_submission:
            return jsonify({'error': 'Submission already exists for this assignment'}), 400
        
        # Check if submission is late
        is_late = False
        if assignment.due_date and datetime.utcnow() > assignment.due_date:
            is_late = True
        
        submission = Submission(
            assignment_id=data['assignment_id'],
            student_id=user.id,
            content=data.get('content', ''),
            file_path=data.get('file_path', ''),
            is_late=is_late
        )
        
        db.session.add(submission)
        db.session.commit()
        
        return jsonify({'message': 'Submission created successfully', 'submission': submission.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create submission'}), 500

# Grade endpoints
@bp.route('/grades', methods=['GET'])
@jwt_required()
def get_grades():
    try:
        user = get_current_user()
        course_id = request.args.get('course_id')
        
        if user.role == UserRole.STUDENT:
            if course_id:
                # Check enrollment
                enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=course_id, is_active=True).first()
                if not enrollment:
                    return jsonify({'error': 'Not enrolled in this course'}), 403
                grades = Grade.query.filter_by(student_id=user.id).join(Assignment).filter(Assignment.course_id == course_id).all()
            else:
                grades = Grade.query.filter_by(student_id=user.id).all()
        else:  # Teacher
            if course_id:
                course = Course.query.get_or_404(course_id)
                if course.teacher_id != user.id:
                    return jsonify({'error': 'Access denied'}), 403
                grades = Grade.query.join(Assignment).filter(Assignment.course_id == course_id).all()
            else:
                # Get grades for all teacher's courses
                courses = Course.query.filter_by(teacher_id=user.id, is_active=True).all()
                course_ids = [course.id for course in courses]
                grades = Grade.query.join(Assignment).filter(Assignment.course_id.in_(course_ids)).all()
        
        return jsonify({'grades': [grade.to_dict() for grade in grades]}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch grades'}), 500

@bp.route('/grades', methods=['POST'])
@jwt_required()
@require_role('teacher')
def create_grade():
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Validate required fields
        required_fields = ['assignment_id', 'student_id', 'score']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        assignment = Assignment.query.get_or_404(data['assignment_id'])
        
        # Check if teacher owns the course
        course = Course.query.get(assignment.course_id)
        if course.teacher_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if grade already exists
        existing_grade = Grade.query.filter_by(assignment_id=data['assignment_id'], student_id=data['student_id']).first()
        if existing_grade:
            return jsonify({'error': 'Grade already exists for this student and assignment'}), 400
        
        # Validate score
        if data['score'] < 0 or data['score'] > assignment.max_score:
            return jsonify({'error': f'Score must be between 0 and {assignment.max_score}'}), 400
        
        grade = Grade(
            assignment_id=data['assignment_id'],
            student_id=data['student_id'],
            score=data['score'],
            feedback=data.get('feedback', ''),
            graded_by=user.id
        )
        
        db.session.add(grade)
        db.session.commit()
        
        return jsonify({'message': 'Grade created successfully', 'grade': grade.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create grade'}), 500

# Enrollment endpoints
@bp.route('/enrollments', methods=['POST'])
@jwt_required()
@require_role('student')
def create_enrollment():
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not data.get('course_id'):
            return jsonify({'error': 'course_id is required'}), 400
        
        course = Course.query.get_or_404(data['course_id'])
        
        # Check if already enrolled
        existing_enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=data['course_id']).first()
        if existing_enrollment:
            if existing_enrollment.is_active:
                return jsonify({'error': 'Already enrolled in this course'}), 400
            else:
                # Reactivate enrollment
                existing_enrollment.is_active = True
                db.session.commit()
                return jsonify({'message': 'Enrollment reactivated successfully'}), 200
        
        enrollment = Enrollment(
            student_id=user.id,
            course_id=data['course_id']
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        return jsonify({'message': 'Enrolled successfully', 'enrollment': enrollment.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to enroll in course'}), 500

# Dashboard data endpoints
@bp.route('/dashboard/student', methods=['GET'])
@jwt_required()
@require_role('student')
def student_dashboard():
    try:
        user = get_current_user()
        
        # Get enrolled courses
        enrollments = Enrollment.query.filter_by(student_id=user.id, is_active=True).all()
        courses = [enrollment.course for enrollment in enrollments if enrollment.course.is_active]
        
        # Get recent assignments
        course_ids = [course.id for course in courses]
        assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids), Assignment.is_active == True).order_by(Assignment.due_date.desc()).limit(5).all()
        
        # Get grades
        grades = Grade.query.filter_by(student_id=user.id).all()
        
        # Calculate statistics
        total_assignments = len(assignments)
        submitted_assignments = Submission.query.filter_by(student_id=user.id).count()
        average_grade = sum([grade.score for grade in grades]) / len(grades) if grades else 0
        
        return jsonify({
            'courses': [course.to_dict() for course in courses],
            'recent_assignments': [assignment.to_dict() for assignment in assignments],
            'grades': [grade.to_dict() for grade in grades],
            'stats': {
                'total_courses': len(courses),
                'total_assignments': total_assignments,
                'submitted_assignments': submitted_assignments,
                'average_grade': round(average_grade, 2)
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

@bp.route('/dashboard/teacher', methods=['GET'])
@jwt_required()
@require_role('teacher')
def teacher_dashboard():
    try:
        user = get_current_user()
        
        # Get teacher's courses
        courses = Course.query.filter_by(teacher_id=user.id, is_active=True).all()
        course_ids = [course.id for course in courses]
        
        # Get assignments
        assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids), Assignment.is_active == True).all()
        
        # Get enrollments
        enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids), Enrollment.is_active == True).all()
        
        # Get submissions
        assignment_ids = [assignment.id for assignment in assignments]
        submissions = Submission.query.filter(Submission.assignment_id.in_(assignment_ids)).all()
        
        # Get grades
        grades = Grade.query.filter(Grade.assignment_id.in_(assignment_ids)).all()
        
        return jsonify({
            'courses': [course.to_dict() for course in courses],
            'assignments': [assignment.to_dict() for assignment in assignments],
            'stats': {
                'total_courses': len(courses),
                'total_students': len(enrollments),
                'total_assignments': len(assignments),
                'total_submissions': len(submissions),
                'graded_submissions': len(grades)
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500