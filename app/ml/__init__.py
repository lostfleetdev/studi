import os
import json
from app.models import User, Grade, Assignment, Course, Enrollment
from app import db

class StudentPerformancePredictor:
    def __init__(self, model_dir='./models'):
        self.model_dir = model_dir
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
    
    def get_performance_insights(self, student_id):
        """Get insights about student performance"""
        try:
            # Get student data
            student = User.query.get(student_id)
            if not student:
                return None
            
            # Get student grades
            grades = Grade.query.filter_by(student_id=student_id).all()
            
            if not grades:
                return {
                    'prediction': {
                        'predicted_performance': 0,
                        'current_performance': 0,
                        'feature_importance': {}
                    },
                    'insights': [{
                        'type': 'neutral',
                        'message': 'No grades available yet. Start submitting assignments to get insights!'
                    }],
                    'recommendations': [
                        'Submit your first assignment to get started',
                        'Stay consistent with assignment submissions',
                        'Ask questions if you need help'
                    ]
                }
            
            # Calculate basic statistics
            scores = [grade.score for grade in grades]
            current_avg = sum(scores) / len(scores)
            
            # Simple prediction based on trend
            if len(scores) >= 3:
                recent_avg = sum(scores[-3:]) / 3
                early_avg = sum(scores[:3]) / 3
                trend = recent_avg - early_avg
                predicted_perf = min(100, max(0, current_avg + trend))
            else:
                predicted_perf = current_avg
            
            # Generate insights
            insights = []
            if predicted_perf > current_avg + 5:
                insights.append({
                    'type': 'positive',
                    'message': f'Your performance is improving! Predicted: {predicted_perf:.1f}%'
                })
            elif predicted_perf < current_avg - 5:
                insights.append({
                    'type': 'warning',
                    'message': f'Your performance may decline. Predicted: {predicted_perf:.1f}%'
                })
            else:
                insights.append({
                    'type': 'neutral',
                    'message': f'Your performance is stable at around {predicted_perf:.1f}%'
                })
            
            # Generate recommendations
            recommendations = []
            if current_avg < 70:
                recommendations.append('Consider seeking help from your instructor')
                recommendations.append('Review study materials and practice more')
            elif current_avg < 85:
                recommendations.append('Keep up the good work!')
                recommendations.append('Focus on consistency in your submissions')
            else:
                recommendations.append('Excellent work! Keep maintaining this level')
                recommendations.append('Consider helping other students')
            
            if len(scores) < 5:
                recommendations.append('Submit more assignments to get better insights')
            
            return {
                'prediction': {
                    'predicted_performance': round(predicted_perf, 2),
                    'current_performance': round(current_avg, 2),
                    'feature_importance': {
                        'consistency': 0.3,
                        'improvement_trend': 0.4,
                        'assignment_completion': 0.3
                    }
                },
                'insights': insights,
                'recommendations': recommendations[:3]  # Top 3 recommendations
            }
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            return None