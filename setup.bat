@echo off
chcp 65001 >nul
echo ============================================
echo   麻将牌谱生成器 - 环境安装
echo ============================================
echo.

echo [1/2] 安装 Python 依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo Python 依赖安装失败，请检查网络或手动运行: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [2/2] 安装天凤转换工具 (Node.js)...
cd /d "%~dp0tenhou\tenhou-convert"
call npm install
if errorlevel 1 (
    echo 天凤转换工具安装失败，请确认已安装 Node.js (https://nodejs.org)
    echo 或手动运行: cd tenhou\tenhou-convert ^&^& npm install
    pause
    exit /b 1
)

echo.
echo ============================================
echo   安装完成！运行: python batch_gui_form_v4.py
echo ============================================
pause