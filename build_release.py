import os
import zipfile

print('Building VAVE Desktop Release...')

start_bat_content = """@echo off
echo Starting VAVE Desktop App...
echo First time setup might take a minute...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\\Scripts\\activate.bat
echo Installing dependencies...
pip install -r requirements.txt >nul 2>&1
echo Launching VAVE...
python jarvis_gui.py
"""
with open('Start_VAVE.bat', 'w') as f:
    f.write(start_bat_content)

zip_filename = 'VAVE_Desktop_App.zip'
if os.path.exists(zip_filename):
    os.remove(zip_filename)

ignore_dirs = ['venv', '.venv', '__pycache__', '.git', '.gemini', 'build', 'dist', 'data']
ignore_files = ['credentials.json', 'token.json', 'token_workspace.json', 'VAVE_Desktop_App.zip', 'config.json']

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file in ignore_files or file.endswith('.db') or file.endswith('.sqlite3'):
                continue
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, '.')
            zipf.write(file_path, arcname)

    # Write a default safe config.json
    default_config = '''{
    "user_name": "User",
    "assistant_name": "VAVE",
    "llm_model": "qwen2.5:3b"
}'''
    zipf.writestr('config.json', default_config)

os.remove('Start_VAVE.bat')
print(f'Done! Created {zip_filename}.')
