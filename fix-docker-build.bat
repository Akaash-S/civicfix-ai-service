@echo off
REM Fix Docker Build Issues

echo ==========================================
echo   Docker Build Fix Script
echo ==========================================
echo.

echo Step 1: Checking Docker status...
docker info >nul 2>&1
if errorlevel 1 (
    echo X Docker is not running
    echo   Please start Docker Desktop and run this script again
    exit /b 1
)
echo √ Docker is running
echo.

echo Step 2: Checking disk space...
docker system df
echo.

echo Step 3: Cleaning Docker cache...
echo This will remove:
echo - All stopped containers
echo - All networks not used by containers
echo - All dangling images
echo - All build cache
echo.
set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled
    exit /b 0
)

docker system prune -a --volumes -f
echo √ Docker cache cleaned
echo.

echo Step 4: Restarting Docker...
echo Please restart Docker Desktop manually:
echo 1. Right-click Docker icon in system tray
echo 2. Click "Quit Docker Desktop"
echo 3. Start Docker Desktop again
echo 4. Wait for Docker to be ready
echo.
pause

echo Step 5: Testing Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo X Docker is not running
    echo   Please start Docker Desktop
    exit /b 1
)
echo √ Docker is ready
echo.

echo Step 6: Attempting build...
docker-compose build --no-cache

if errorlevel 1 (
    echo.
    echo X Build failed
    echo.
    echo Try these additional steps:
    echo 1. Check your internet connection
    echo 2. Disable VPN if using one
    echo 3. Check Windows Firewall settings
    echo 4. Restart your computer
    echo 5. Reinstall Docker Desktop
    exit /b 1
)

echo.
echo ==========================================
echo   √ Build successful!
echo ==========================================
echo.
echo You can now run: docker-compose up
