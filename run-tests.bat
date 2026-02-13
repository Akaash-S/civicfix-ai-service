@echo off
REM Automated Test Runner for CivicFix AI Service (Windows)

echo ==========================================
echo   CivicFix AI Service - Test Runner
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo X Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

echo √ Docker is running
echo.

REM Check if port 8080 is available
netstat -an | findstr ":8080.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo ! Port 8080 is already in use
    echo   Stop the service using that port or change the port in docker-compose.yml
    exit /b 1
)

echo √ Port 8080 is available
echo.

REM Build and start service
echo Building and starting service...
docker-compose up -d --build

if errorlevel 1 (
    echo X Failed to start service
    exit /b 1
)

echo √ Service started
echo.

REM Wait for service to be ready
echo Waiting for service to be ready...
set max_attempts=30
set attempt=0

:wait_loop
curl -s http://localhost:8080/health >nul 2>&1
if not errorlevel 1 goto service_ready

set /a attempt+=1
if %attempt% geq %max_attempts% (
    echo X Service did not start in time
    echo.
    echo Logs:
    docker-compose logs
    docker-compose down
    exit /b 1
)

timeout /t 1 /nobreak >nul
goto wait_loop

:service_ready
echo √ Service is ready!
echo.

REM Run tests
echo Running tests...
echo.

python test_local.py
set test_result=%errorlevel%

echo.

REM Stop service
echo Stopping service...
docker-compose down

echo.

REM Exit with test result
if %test_result% equ 0 (
    echo ==========================================
    echo   √ All tests passed!
    echo ==========================================
    echo.
    echo Your service is ready to deploy!
    echo Run: gcloud builds submit --config cloudbuild.yaml
    exit /b 0
) else (
    echo ==========================================
    echo   X Tests failed
    echo ==========================================
    echo.
    echo Fix the issues above before deploying.
    exit /b 1
)
