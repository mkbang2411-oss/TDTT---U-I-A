@echo off
color 0A
title Food Map - Auto Deploy Script

echo ============================================
echo    FOOD MAP - AUTO DEPLOYMENT SCRIPT
echo ============================================
echo.

REM Di chuyen den thu muc project
cd /d D:\Food_map

echo [1/5] Cleaning old containers...
docker-compose down 2>nul
docker stop cloudflared 2>nul
docker rm cloudflared 2>nul
echo Done!
echo.

echo [2/5] Starting Docker containers...
docker-compose up -d
echo Waiting for containers to start...
timeout /t 15 /nobreak
echo Done!
echo.

echo [3/5] Checking container status...
docker-compose ps
echo.

echo [4/5] Getting network name...
for /f "tokens=*" %%i in ('docker network ls --filter "name=app-network" --format "{{.Name}}"') do set NETWORK_NAME=%%i
echo Using network: %NETWORK_NAME%
echo.

echo [5/5] Creating Cloudflare Tunnel...
docker run -d --name cloudflared --network %NETWORK_NAME% cloudflare/cloudflared:latest tunnel --url http://nginx:80
echo Waiting for tunnel to connect...
timeout /t 10 /nobreak
echo Done!
echo.

echo [6/6] Getting public link...
echo ============================================
echo.
docker logs cloudflared | findstr "https://"
echo.
echo ============================================
echo.
echo COPY THE LINK ABOVE AND SHARE WITH FRIENDS!
echo.
echo Press any key to keep this window open...
pause >nul