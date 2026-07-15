@echo off
REM ============================================================
REM  แพ็ก MarkItSwift เป็นไฟล์ .exe เดียว ด้วย PyInstaller
REM  วิธีใช้: ดับเบิลคลิกไฟล์นี้ หรือรันในคอมมานด์พรอมต์
REM ============================================================

echo [1/2] ติดตั้ง dependencies...
pip install -r requirements.txt

echo [2/2] กำลังสร้าง .exe...
pyinstaller --noconfirm --onefile --windowed ^
  --name "MarkItSwift" ^
  --icon "app.ico" ^
  --add-data "app.ico;." ^
  --collect-all customtkinter ^
  --collect-all markitdown ^
  --collect-all magika ^
  --collect-all tkinterdnd2 ^
  markitdown_ui.py

echo.
echo เสร็จแล้ว! ไฟล์อยู่ที่: dist\MarkItSwift.exe
pause
