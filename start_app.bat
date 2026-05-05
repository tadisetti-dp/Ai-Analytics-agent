
start cmd /k "cd backend && echo Installing dependencies... && pip install -r requirements.txt && echo Starting Flask App... && python app.py"

echo [2/2] Starting Frontend Application (React)...
start cmd /k "cd frontend && echo Installing dependencies... && npm install && echo Starting React App... && npm start"

echo ===================================================
echo   Both services are starting in new windows.
echo   Please check the new windows for logs.
echo ===================================================
pause
