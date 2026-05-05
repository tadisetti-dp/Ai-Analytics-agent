import sqlite3
import datetime

DB_NAME = "knowledge_history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            created_at DATETIME
        )
    ''')
    try:
        cursor.execute("ALTER TABLE Users ADD COLUMN role TEXT DEFAULT 'user'")
    except sqlite3.OperationalError:
        pass # Column already exists

    # Create AnalysisLogs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AnalysisLogs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_name TEXT,
            target_column TEXT,
            problem_type TEXT,
            model_used TEXT,
            r2_score REAL,
            rmse REAL,
            accuracy REAL,
            f1_score REAL,
            created_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def log_analysis(user_id, file_name, target_column, problem_type, model_used, r2_score, rmse, accuracy, f1_score):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO AnalysisLogs (user_id, file_name, target_column, problem_type, model_used, r2_score, rmse, accuracy, f1_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, file_name, target_column, problem_type, model_used, r2_score, rmse, accuracy, f1_score, datetime.datetime.now()))
    conn.commit()
    conn.close()

def create_user(name, email, password_hash):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                       (name, email, password_hash, datetime.datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, email, password_hash, role FROM Users WHERE LOWER(email) = LOWER(?)", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, email, password_hash, role FROM Users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_analysis_history(user_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = '''
        SELECT file_name, target_column, model_used, problem_type, r2_score, rmse, accuracy, f1_score, created_at 
        FROM AnalysisLogs 
    '''
    params = ()
    if user_id is not None:
        query += "WHERE user_id = ? "
        params = (user_id,)
        
    query += "ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    
    # Format as dict list
    result = []
    for log in logs:
        prob_type = log[3]
        if prob_type == "Regression":
            r2 = round(log[4], 4) if log[4] is not None else 0.0000
            rmse = round(log[5], 4) if log[5] is not None else 0.0000
            metrics = f"R²: {r2} | RMSE: {rmse}"
            score = log[4]
        elif prob_type == "Classification":
            acc = round(log[6], 4) if log[6] is not None else 0.0000
            f1 = round(log[7], 4) if log[7] is not None else 0.0000
            metrics = f"Acc: {acc} | F1: {f1}"
            score = log[6]
        else:
            metrics = "-"
            score = log[4] if log[4] is not None else log[6]

        result.append({
            "dataset": log[0],
            "target": log[1],
            "model": log[2],
            "score": score,
            "problem_type": prob_type if prob_type else "-",
            "metrics": metrics,
            "date": log[8],
            "accuracy": log[6],
            "rmse": log[5]
        })
    return result
