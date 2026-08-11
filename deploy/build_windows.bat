@echo off
echo ===================================================================
echo   COMPILATION DE LINELIST CLEANER (.EXE STANDALONE WINDOWS)
echo ===================================================================
echo.

echo [1/3] Installation des dependances et de PyInstaller...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Compilation de l'executable avec Linelist_Cleaner.spec...
pyinstaller --clean Linelist_Cleaner.spec

echo.
echo [3/3] Creation de l'archive ZIP...
powershell -Command "Compress-Archive -Path dist\Linelist_Cleaner.exe, README.md, LICENSE -DestinationPath Linelist_Cleaner_Windows_x64.zip -Force"

echo.
echo ===================================================================
echo [SUCCES] L'executable autonome est pret dans dist\Linelist_Cleaner.exe
echo Archive portable : Linelist_Cleaner_Windows_x64.zip
echo ===================================================================
pause
