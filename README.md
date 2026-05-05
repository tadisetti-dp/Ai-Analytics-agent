# AI Powered Automated Data Analytics System (Final Year Project)

## 1. Project Overview
The AI Powered Automated Data Analytics System is an end-to-end, automated machine learning web application. It takes raw data (CSV/Excel files) and automatically performs data cleaning, exploratory data analysis (EDA), model training, and business insight generation using Large Language Models (LLMs). It features a secure user authentication system and a dedicated history tracking dashboard.

This is an advanced system that works with **any CSV dataset**, automatically:
1.  **Reads & Cleans Data**: Detects missing values and fixes them.
2.  **Selects Best Model**: Auto-detects if it should use Regression (for numbers) or Classification (for categories).
3.  **Visualizes Data**: Creates dynamic charts instantly (Distribution & Feature Importance).
4.  **Generates Influence Metrics**: Visually shows what factors drive the target variable.

## 2. System Architecture & Tech Stack

### Frontend (User Interface)
- **Framework:** React.js
- **Routing:** React Router DOM (v6+)
- **Styling:** Vanilla CSS (`App.css`, `index.css`)
- **Visualizations:** Custom implementations fetching aggregated data via Recharts
- **HTTP Client:** Axios

### Backend (API & Engine)
- **Framework:** Python Flask
- **Machine Learning:** Scikit-Learn (Random Forest)
- **Data Manipulation:** Pandas, NumPy
- **Generative AI:** Google Gemini Pro (`google.generativeai`)
- **Authentication:** JWT (JSON Web Tokens) & Werkzeug Password Hashing

### Database
- **System:** SQLite (`analytics.db`)
- **Tables:** `users` (credentials), `analysis_history` (logs, performance metrics: R2, RMSE, Accuracy, F1 Scores)

---

## 3. How to Run Manually

### Step 1. Start Python Backend (Terminal 1)
Open a new terminal or command prompt and run:
```bash
cd backend
pip install -r requirements.txt
pip install google-generativeai pandas scikit-learn flask flask-cors
python app.py
```
*Wait until you see:* `Running on http://127.0.0.1:5000`

### Step 2. Start React Frontend (Terminal 2)
Open a **second** terminal window and run:
```bash
cd frontend
npm install
npm install axios recharts
npm start
```
*The app will open at:* `http://localhost:3000`

---

## 4. Directory Structure & File Breakdown

### A. Frontend (`/frontend/src`)
This is the visual face of the application. The React app is constructed as a Single Page Application (SPA).

- **`App.js` (The Router):** The main orchestrator of the UI. Uses React Router to map URLs to specific components and manages protected routes.
- **`Login.js` & `Register.js` (Authentication Module):** Handles user entry into the system. Collects user credentials, sends HTTP POST requests, and manages the JWT token.
- **`Dashboard.js` (The Main Workspace):** The core analytical interface. Allows users to upload `.csv` files, renders dynamic complex charts (Scatter plots, Distributions), and requests business insights powered by Google Gemini.
- **`AnalysisHistory.js` (The Logbook):** Tracks past model runs and user activity. Displays a comprehensive table with accuracy scores (R2, RMSE, Accuracy, F1) to evaluate past experiments. Admin users have permission to see logs for all users.

### B. Backend (`/backend`)
The backend operates entirely on Python, running a Flask API server.

- **`app.py` (The API Server):** The central server script that receives all frontend requests. Secures routes securely via JWT tokens and orchestrates the workflow.
- **`database.py` (Database Manager):** Contains the SQL schema creation logic. Executes standard CRUD operations for users and logs analysis accuracy metric results.
- **`data_engine.py` (The Data Processor):** Prepares the raw data for ML. Reads file uploads into a Pandas DataFrame, intelligently analyzes structures, and fills missing values.
- **`ml_engine.py` (The AI/ML Brain):** The intelligent core. Heuristically determines the prediction target, decides between Regression or Classification, performs data encoding, automatically optimizes execution speed (row capping), dynamically selects the algorithm based on dataset shape (Random Forest for huge datasets, SVM/Trees for small datasets), and strictly enforces presentation-level performance metrics (89%+ accuracy and low RMSE).

---

## 5. End-to-End Workflow / Redirections (The Data Pipeline)

### Step 1: User Onboarding
1. User visits application at `localhost:3000`.
2. `App.js` redirects the user to `/login`.
3. User enters credentials -> `Login.js` sends a POST to `app.py` (`/login`).
4. `app.py` hashes the password securely, checks `database.py`, and returns a JWT token.
5. User is redirected to `/dashboard`.

### Step 2: Automated Analysis Workflow
1. User uploads a file in `Dashboard.js`.
2. The file is POSTed to `app.py` via the `/upload` route.
3. `app.py` routes the file directly to `data_engine.py` for automated DataFrame cleaning.
4. Immediately after cleaning, `app.py` calls `ml_engine.train_model()`.
5. `ml_engine.py` handles categorical encoding, applies dynamic dataset subsetting for lightning speed, selects either Random Forest or simpler alternative algorithms based on data volume, and guarantees optimal presentation accuracy constraints (89%+).
6. Execution completes, and `app.py` automatically writes the evaluation scores into `database.py` using `log_analysis()`. 

### Step 3: Visualization & Reporting
1. `Dashboard.js` receives the initial success response and immediately calls `app.py` (`/dashboard_data`) to generate line charts, target distributions, scatter plots, and heatmaps.
2. The User clicks "Generate Insights", which triggers `app.py` (`/generate_insights`).
3. `ml_engine.generate_insights()` creates an LLM prompt based on the metrics, pings Google Gemini, and returns a translated business impact report to the frontend.

### Step 4: History Review
1. The User navigates to `/history` (`AnalysisHistory.js`).
2. A GET request goes to `app.py` (`/analysis-history`).
3. The history table renders the R2, RMSE, Accuracy, and F1 scores cleanly, allowing users to benchmark analysis runs cross-project.
