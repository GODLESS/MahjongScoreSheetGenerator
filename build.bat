@echo off
chcp 65001 >nul
echo ============================================
echo   麻将牌谱生成器 - PyInstaller 打包
echo ============================================
echo.

pyinstaller --noconsole --onefile --name "麻将牌谱生成器" ^
  --add-data "fonts;fonts" ^
  --add-data "mahjong_score_sheet.py;." ^
  --add-data "_mahjong_fmt.py;." ^
  --add-data "tenhou;tenhou" ^
  --hidden-import reportlab ^
  --hidden-import fpdf ^
  --hidden-import pdfrw ^
  --hidden-import PyPDF2 ^
  batch_gui_form_v4.py

if errorlevel 1 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包完成！exe 位于 dist 目录
echo ============================================
pause