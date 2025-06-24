@echo off
chcp 65001
cd /d %~dp0

netstat -ano | findstr ":5000"
if %errorlevel%==0 (
    echo 端口 5000 已被占用，api无法正常运行
) else (
    echo 端口 5000 未被占用。
)

REM 打印请求格式说明
echo.
echo ================================
echo Yukkuri API 启动说明
echo ----------------
echo 1. 端口: 5000
echo 2. 合成接口: POST /synthesize
echo    Content-Type: application/json
echo    请求体示例:
echo    {
echo      "text": "你好，世界",
echo      "voice": "aq_yukkuri.phont",
echo      "speed": 100,
echo      "pitch": 100,
echo      "volume": 100
echo    }
echo    返回: audio/wav 文件
echo 3. 获取音色列表: GET /voices
echo ================================
echo.

REM 启动 API 服务
python-3.9.11-embed-win32\python.exe api.py

pause