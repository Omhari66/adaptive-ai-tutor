@echo off
cd backend
echo starting backend ....
start cmd /k "uvicorn app.main:app --reload"

echo starting frontend ....
cd ..
start cmd /k "npm run dev"