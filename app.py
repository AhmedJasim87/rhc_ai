from flask import Flask, render_template, request, jsonify, session
import json
import random
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for sessions

# Enhanced medical knowledge base
with open('knowledge_base.json') as f:
    knowledge_base = json.load(f)

# Symptom severity weights with time modifiers
SEVERITY_WEIGHTS = {
    'mild': 1,
    'moderate': 2,
    'severe': 3
}

TIME_MODIFIERS = {
    'less than 24 hours': 0.8,
    '1-3 days': 1.0,
    '4-7 days': 1.2,
    'more than 1 week': 1.5
}

# User session management
@app.before_request
def init_session():
    if 'history' not in session:
        session['history'] = []
    if 'user_id' not in session:
        session['user_id'] = random.randint(10000, 99999)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check_symptoms', methods=['POST'])
def check_symptoms():
    try:
        data = request.json
        symptoms = [s.strip().lower() for s in data.get('symptoms', []) if s.strip()]
        duration = data.get('duration', '')
        severity = data.get('severity', '')
        
        if not symptoms:
            return jsonify({'error': 'Please enter at least one symptom'}), 400

        # Enhanced analysis
        possible_conditions = analyze_symptoms(symptoms, duration, severity)
        recommendations = get_recommendations(possible_conditions, severity)
        
        # Log this check in session history
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'symptoms': symptoms,
            'possible_conditions': possible_conditions,
            'severity': severity
        }
        session['history'].append(log_entry)
        session.modified = True
        
        return jsonify({
            'possible_conditions': possible_conditions,
            'recommendations': recommendations,
            'user_id': session['user_id']
        })
    
    except Exception as e:
        app.logger.error(f"Error processing symptoms: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/history')
def get_history():
    return jsonify({
        'user_id': session['user_id'],
        'history': session.get('history', [])
    })

def analyze_symptoms(symptoms, duration, severity):
    """Enhanced symptom analysis with time and severity weighting"""
    condition_scores = {}
    
    for condition, data in knowledge_base['conditions'].items():
        # Calculate symptom matches with partial matching
        matched_symptoms = []
        for user_symptom in symptoms:
            for known_symptom in data['symptoms']:
                if user_symptom in known_symptom or known_symptom in user_symptom:
                    matched_symptoms.append(known_symptom)
                    break
        
        if matched_symptoms:
            # Base score with partial matches
            base_score = len(matched_symptoms) / len(data['symptoms'])
            
            # Apply severity and duration modifiers
            severity_mod = SEVERITY_WEIGHTS.get(severity, 1)
            time_mod = TIME_MODIFIERS.get(duration, 1)
            
            # Calculate final score
            final_score = base_score * severity_mod * time_mod
            condition_scores[condition] = {
                'score': final_score,
                'matched_symptoms': matched_symptoms
            }
    
    # Sort by score and return top 3
    sorted_conditions = sorted(condition_scores.items(), 
                             key=lambda x: x[1]['score'], 
                             reverse=True)[:3]
    
    return [cond[0] for cond in sorted_conditions]

def get_recommendations(conditions, severity):
    """Generate personalized recommendations"""
    recommendations = []
    
    # Severity-based advice
    if severity == 'mild':
        recommendations.append("Your symptoms seem mild but should be monitored.")
    elif severity == 'moderate':
        recommendations.append("Moderate symptoms may require professional evaluation soon.")
    else:
        recommendations.append("Severe symptoms warrant immediate medical attention.")
    
    # Condition-specific advice
    for condition in conditions[:2]:
        if condition in knowledge_base['recommendations']:
            rec = knowledge_base['recommendations'][condition]
            recommendations.append(f"For {condition}: {rec}")
    
    # General health tips
    general_tips = random.choice([
        "Stay hydrated and get adequate rest.",
        "Monitor your temperature regularly.",
        "Avoid strenuous activity while symptomatic."
    ])
    recommendations.append(general_tips)
    
    # Always include disclaimer
    recommendations.append(
        "Remember: This tool doesn't replace professional medical advice."
    )
    
    return recommendations

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
