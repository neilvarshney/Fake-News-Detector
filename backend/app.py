from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from models import db, User, Analysis
from auth import auth_bp
import os
from dotenv import load_dotenv
import joblib
import torch
import numpy as np
from transformers import BertTokenizer, BertModel
from datetime import timedelta

load_dotenv()


app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fake_news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Create database tables
with app.app_context():
    db.create_all()

# Load BERT components
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertModel.from_pretrained('bert-base-uncased')
model = joblib.load("bert_fake_news_model.pkl")

def get_bert_embedding(text):
    inputs = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )
    with torch.no_grad():
        outputs = bert_model(**inputs)
    return outputs.last_hidden_state[:,0,:].numpy()

@app.errorhandler(422)
def handle_validation_error(err):
    return jsonify({'error': 'Invalid request data'}), 422

@app.errorhandler(401)
def handle_auth_error(err):
    return jsonify({'error': 'Authentication required'}), 401

@app.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_text():
    try:
        print("Received request headers:", dict(request.headers))
        print("Received request data:", request.get_json())
        
        data = request.get_json()
        if not data or 'text' not in data:
            print("Error: No text in request data")
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        if not text.strip():
            print("Error: Empty text")
            return jsonify({'error': 'Text cannot be empty'}), 400
            
        current_user_id = get_jwt_identity()
        print("Current user ID:", current_user_id)
        
        if not current_user_id:
            print("Error: No user ID found")
            return jsonify({'error': 'Invalid user session'}), 401
        
        # Convert string ID to integer for database query
        user_id = int(current_user_id)
        
        # Generate BERT embedding
        embedding = get_bert_embedding(text)
        
        # Predict
        prediction = model.predict(embedding)[0]
        confidence = model.predict_proba(embedding)[0].max()
        result = 'Real' if prediction == 1 else 'Fake'
        
        # Save analysis to database
        analysis = Analysis(
            user_id=user_id,  # Use the converted integer ID
            text=text,
            result=float(prediction),
            confidence=float(confidence)
        )
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({
            'result': result,
            'confidence': float(confidence)
        })
    except Exception as e:
        print(f"Error in analyze_text: {str(e)}")
        import traceback
        print("Full traceback:", traceback.format_exc())
        return jsonify({'error': f'An error occurred during analysis: {str(e)}'}), 500

@app.route('/analysis-history', methods=['GET'])
@jwt_required()
def get_analysis_history():
    current_user_id = get_jwt_identity()
    analyses = Analysis.query.filter_by(user_id=current_user_id).order_by(Analysis.created_at.desc()).all()
    
    return jsonify([{
        'id': analysis.id,
        'text': analysis.text[:50] + '...',
        'result': 'Real' if analysis.result == 1 else 'Fake',
        'confidence': analysis.confidence,
        'timestamp': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for analysis in analyses])

@app.route('/analysis/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_analysis(analysis_id):
    current_user_id = get_jwt_identity()
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user_id).first()
    
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    return jsonify({
        'id': analysis.id,
        'text': analysis.text,
        'result': 'Real' if analysis.result == 1 else 'Fake',
        'confidence': analysis.confidence,
        'timestamp': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')

    })

@app.route('/analysis/<int:analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis(analysis_id):
    current_user_id = get_jwt_identity()
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user_id).first()
    
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    db.session.delete(analysis)
    db.session.commit()
    
    return jsonify({'message': 'Analysis deleted successfully'}), 200


if __name__ == '__main__':
    app.run(debug=True)