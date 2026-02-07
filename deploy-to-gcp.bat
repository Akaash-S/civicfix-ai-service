@echo off
REM CivicFix AI Service - Google Cloud Platform Deployment Script (Windows)
REM This script automates the deployment process to Cloud Run

setlocal enabledelayedexpansion

echo ========================================
echo   CivicFix AI Service - GCP Deployment
echo ========================================
echo.

REM Configuration
set "REGION=us-central1"
set "SERVICE_NAME=civicfix-ai-service"

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo [31mError: gcloud CLI is not installed[0m
    echo Please install it from: https://cloud.google.com/sdk/docs/install
    exit /b 1
)

REM Check if project ID is set
if "%GCP_PROJECT_ID%"=="" (
    echo [33mProject ID not set. Please enter your GCP Project ID:[0m
    set /p GCP_PROJECT_ID=
    
    if "!GCP_PROJECT_ID!"=="" (
        echo [31mError: Project ID is required[0m
        exit /b 1
    )
)

echo [32m[PASS][0m Using Project ID: %GCP_PROJECT_ID%
echo [32m[PASS][0m Using Region: %REGION%
echo.

REM Set project
echo Setting GCP project...
gcloud config set project %GCP_PROJECT_ID%

REM Enable required APIs
echo Enabling required APIs...
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com secretmanager.googleapis.com --quiet

echo [32m[PASS][0m APIs enabled
echo.

REM Check secrets
echo Checking secrets...

REM Function to create secret if not exists
call :check_secret "database-url" "Please enter your DATABASE_URL:"
call :check_secret "ai-service-api-key" "Please enter your API_KEY:"
call :check_secret "ai-service-secret-key" "Please enter your SECRET_KEY:"

echo.

REM Grant Cloud Run access to secrets
echo Granting Cloud Run access to secrets...
for /f "tokens=*" %%i in ('gcloud projects describe %GCP_PROJECT_ID% --format="value(projectNumber)"') do set PROJECT_NUMBER=%%i

for %%s in (database-url ai-service-api-key ai-service-secret-key) do (
    gcloud secrets add-iam-policy-binding %%s --member="serviceAccount:%PROJECT_NUMBER%-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" --quiet 2>nul
)

echo [32m[PASS][0m Secrets configured
echo.

REM Build and deploy
echo Building and deploying to Cloud Run...
echo This may take 5-10 minutes...
echo.

gcloud builds submit --config cloudbuild.yaml

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================
echo.

REM Get service URL
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format "value(status.url)"') do set SERVICE_URL=%%i

echo [32m[PASS][0m Service deployed successfully!
echo.
echo Service URL: %SERVICE_URL%
echo.
echo Next steps:
echo 1. Test the service:
echo    curl %SERVICE_URL%/health
echo.
echo 2. Update your backend .env file:
echo    AI_SERVICE_URL=%SERVICE_URL%
echo.
echo 3. View logs:
echo    gcloud run services logs tail %SERVICE_NAME% --region %REGION%
echo.
echo 4. Monitor service:
echo    https://console.cloud.google.com/run/detail/%REGION%/%SERVICE_NAME%
echo.
echo [32mDeployment successful![0m
goto :eof

:check_secret
set secret_name=%~1
set secret_prompt=%~2

gcloud secrets describe %secret_name% >nul 2>nul
if %errorlevel% equ 0 (
    echo [32m[PASS][0m Secret '%secret_name%' already exists
) else (
    echo [33m%secret_prompt%[0m
    set /p secret_value=
    
    if "!secret_value!"=="" (
        echo [31mError: Secret value cannot be empty[0m
        exit /b 1
    )
    
    echo !secret_value! | gcloud secrets create %secret_name% --data-file=-
    echo [32m[PASS][0m Secret '%secret_name%' created
)
goto :eof
