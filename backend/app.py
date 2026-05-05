from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import io

from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import datetime

# Import our new engines
from data_engine import DataEngine
from ml_engine import MLEngine
import database

app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app)

app.config['SECRET_KEY'] = 'your-secret-key-12345'
# Initialize database
database.init_db()

# Global instances to hold state
data_engine = DataEngine()
ml_engine = MLEngine()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            token = auth_header.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except Exception as e:
            return jsonify({'error': 'Token is invalid!'}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
def home():
    # Serve React App on the root URL
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return app.send_static_file('index.html')
    return jsonify({"status": "AI Analytics System Running Successfully"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
        
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    if database.create_user(name, email, hashed_password):
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"error": "Email already exists"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Fallbacks for admin login convenience
    if email.lower() == 'admin':
        email = 'admin@test.com'
    if email.lower() == 'admin@test.com' and password == 'admin':
        password = 'admin123'
    
    user = database.get_user_by_email(email)
    if not user or not check_password_hash(user[3], password):
        return jsonify({"error": "Invalid email or password"}), 401
        
    token = jwt.encode({
        'user_id': user[0],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({"token": token, "name": user[1], "user_id": user[0]}), 200

@app.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/analysis-history/<int:user_id>", methods=["GET"])
@token_required
def analysis_history(current_user_id, user_id):
    # Fetch user role
    user = database.get_user_by_id(current_user_id)
    role = user[4] if user else 'user'
    
    # Block access if not admin and requesting another user's history
    if role != 'admin' and current_user_id != user_id:
        return jsonify({"error": "Unauthorized to access this history"}), 403
        
    # Admin gets all data, regular user gets only their data
    target_id = None if role == 'admin' else user_id
    history = database.get_analysis_history(target_id)
    return jsonify({"history": history})

@app.route("/upload", methods=["POST"])
@token_required
def upload_file(current_user_id):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        success, message = data_engine.load_data(file)
        if success:
            # Trigger Auto-Analysis immediately
            structure = data_engine.analyze_structure()
            data_engine.auto_clean() 
            
            # --- AUTO ML TRIGGER ---
            # Train a model automatically on upload for immediate results
            try:
                # We pass the full dataframe to the ML engine
                ml_results = ml_engine.train_model(data_engine.df)
                
                # Fetch score gracefully based on problem type
                score = None
                if ml_results.get("type") == "Regression":
                     score = ml_results.get("test_score_r2")
                elif ml_results.get("type") == "Classification":
                     score = ml_results.get("accuracy")

                if score is not None:
                     database.log_analysis(
                          user_id=current_user_id,
                          file_name=file.filename,
                          target_column=ml_results.get("target_column"),
                          problem_type=ml_results.get("type"),
                          model_used=ml_results.get("model"),
                          r2_score=ml_results.get("test_score_r2") if ml_results.get("type") == "Regression" else None,
                          rmse=ml_results.get("rmse") if ml_results.get("type") == "Regression" else None,
                          accuracy=ml_results.get("accuracy") if ml_results.get("type") == "Classification" else None,
                          f1_score=ml_results.get("f1_score") if ml_results.get("type") == "Classification" else None
                     )
            except Exception as e:
                print(f"Auto-ML Error: {e}")
                ml_results = {"error": str(e), "message": "Auto-ML failed or skipped"}

            preview = data_engine.get_preview()
            stats = data_engine.get_summary_stats()
            
            return jsonify({
                "message": "File uploaded, analyzed, and modeled successfully",
                "structure": structure,
                "preview": preview,
                "summary_stats": stats,
                "ml_results": ml_results
            })
        else:
            return jsonify({"error": f"Failed to process file: {message}"}), 500

@app.route("/generate_insights", methods=["POST"])
@token_required
def generate_insights(current_user_id):
    """Generates a text report using LLM."""
    if data_engine.df is None:
         return jsonify({"error": "No data available. Please upload a file first."}), 400

    # Get API Key from request body
    data = request.get_json()
    user_api_key = data.get('apiKey') if data else None

    try:
        # Prepare summaries for the LLM
        # Limit summary stats to avoid token limits
        summary_stats = str(data_engine.get_summary_stats())[:2000] 
        
        ml_summary = {
            "target_column": ml_engine.target_col,
            "problem_type": ml_engine.model_type,
        }
        
        insights = ml_engine.generate_insights(summary_stats, str(ml_summary), api_key=user_api_key)
        return jsonify({"insights": insights})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard_data", methods=["GET"])
@token_required
def dashboard_data(current_user_id):
    """Returns aggregated data for frontend charts."""
    if data_engine.df is None:
        return jsonify({"error": "No data loaded"}), 400
    
    charts = {}
    
    # 1. Target Distribution (if target identified)
    if ml_engine.target_col:
        target = ml_engine.target_col
        try:
            if ml_engine.model_type == "Regression":
                # For regression, bin the data for histogram
                counts, bins = pd.cut(data_engine.df[target], bins=10, retbins=True)
                # Convert intervals to string labels
                counts = counts.value_counts().sort_index()
                charts['target_distribution'] = {str(k): int(v) for k, v in counts.items()}
            else:
                # For classification, just value counts
                counts = data_engine.df[target].value_counts()
                charts['target_distribution'] = {str(k): int(v) for k, v in counts.items()}
        except Exception as e:
            print(f"Chart generation error: {e}")
            charts['target_distribution'] = {}

    # 2. Scatter Plot (Feature vs Target)
    try:
        if ml_engine.target_col:
             # Find the numeric column with highest correlation to target (or just first numeric)
            numeric_cols = data_engine.df.select_dtypes(include=[np.number]).columns.tolist()
            if ml_engine.target_col in numeric_cols:
                numeric_cols.remove(ml_engine.target_col)
            
            if numeric_cols:
                # Use the first available numeric column for scatter against target
                feature_col = numeric_cols[0]
                # Limit to 500 points for performance
                sample_df = data_engine.df.sample(min(500, len(data_engine.df)))
                scatter_data = []
                for _, row in sample_df.iterrows():
                    scatter_data.append({
                        "x": row[feature_col],
                        "y": row[ml_engine.target_col]
                    })
                charts['scatter_plot'] = {
                    "feature": feature_col,
                    "target": ml_engine.target_col,
                    "data": scatter_data
                }
    except Exception as e:
        print(f"Scatter plot error: {e}")

    # 3. Line Chart (Date vs Target/First Numeric)
    try:
        date_cols = data_engine.meta.get('types', {}).get('date', [])
        if date_cols:
            date_col = date_cols[0]
            # Convert to datetime if not already
            temp_df = data_engine.df.copy()
            temp_df[date_col] = pd.to_datetime(temp_df[date_col])
            
            # Group by date and mean of target (if numeric) or count
            if ml_engine.target_col and pd.api.types.is_numeric_dtype(temp_df[ml_engine.target_col]):
                 line_data_df = temp_df.groupby(temp_df[date_col].dt.date)[ml_engine.target_col].mean().reset_index()
                 y_axis = ml_engine.target_col
            else:
                 # Just count rows per date
                 line_data_df = temp_df.groupby(temp_df[date_col].dt.date).size().reset_index(name='count')
                 y_axis = 'count'
            
            # Sort by date
            line_data_df = line_data_df.sort_values(by=date_col)
            
            line_chart_data = []
            for _, row in line_data_df.iterrows():
                 line_chart_data.append({
                     "x": str(row[date_col]),
                     "y": row[y_axis]
                 })
            
            charts['line_chart'] = {
                "x_label": date_col,
                "y_label": y_axis,
                "data": line_chart_data
            }
    except Exception as e:
        print(f"Line chart error: {e}")

    # 4. Correlation Matrix (Numeric only)
    try:
        corr = data_engine.df.select_dtypes(include=[np.number]).corr()
        # Format for heatmap: x, y, value
        heatmap_data = []
        for x in corr.columns:
            for y in corr.columns:
                heatmap_data.append({"x": x, "y": y, "value": round(corr.loc[x, y], 2)})
        charts['correlation_heatmap'] = heatmap_data
    except:
        charts['correlation_heatmap'] = []

    return jsonify(charts)

# --- DEPLOYMENT CONFIGURATION ---
@app.errorhandler(404)
@app.errorhandler(405)
def not_found(e):
    # Fallback to React's index.html for client-side routing (handles both 404 and GET requests to POST routes)
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return app.send_static_file('index.html')
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)