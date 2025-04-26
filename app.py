from flask import Flask, render_template, request, jsonify
import json
from collections import Counter

app = Flask(__name__)

# Medical knowledge base
with open('knowledge_base.json') as f:
    knowledge_base = json.load(f)

# Symptom severity weights
SEVERITY_WEIGHTS = {
    'mild': 1,
    'moderate': 2,
    'severe': 3
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check_symptoms', methods=['POST'])
def check_symptoms():
    try:
        data = request.json
        symptoms = data.get('symptoms', [])
        duration = data.get('duration', '')
        severity = data.get('severity', '')
        
        if not symptoms:
            return jsonify({'error': 'No symptoms provided'}), 400

        # Calculate possible conditions
        possible_conditions = analyze_symptoms(symptoms, duration, severity)
        
        # Get recommendations
        recommendations = get_recommendations(possible_conditions, severity)
        
        return jsonify({
            'possible_conditions': possible_conditions,
            'recommendations': recommendations
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_symptoms(symptoms, duration, severity):
    """Analyze symptoms and return possible conditions"""
    condition_scores = Counter()
    
    for condition, data in knowledge_base['conditions'].items():
        # Check how many of the condition's symptoms match user input
        common_symptoms = set(symptoms) & set(data['symptoms'])
        if common_symptoms:
            # Base score is number of matching symptoms
            score = len(common_symptoms)
            
            # Adjust by severity if available
            if severity in SEVERITY_WEIGHTS:
                score *= SEVERITY_WEIGHTS[severity]
                
            condition_scores[condition] = score
    
    # Get top 3 most likely conditions
    most_likely = [condition for condition, _ in condition_scores.most_common(3)]
    
    return most_likely

def get_recommendations(conditions, severity):
    """Generate recommendations based on conditions and severity"""
    recommendations = []
    
    # General advice based on severity
    if severity == 'mild':
        recommendations.append("Your symptoms seem mild. Monitor them and consider over-the-counter remedies.")
    elif severity == 'moderate':
        recommendations.append("Your symptoms are moderate. You may want to consult a healthcare provider soon.")
    else:
        recommendations.append("Your symptoms seem severe. Please seek medical attention immediately.")
    
    # Specific advice for conditions
    for condition in conditions[:2]:  # Limit to top 2 conditions
        if condition in knowledge_base['recommendations']:
            recommendations.append(knowledge_base['recommendations'][condition])
    
    # Always include general advice
    recommendations.append("This is not a substitute for professional medical advice. Always consult a doctor for proper diagnosis.")
    
    return recommendations

if __name__ == '__main__':
    app.run(debug=True)
