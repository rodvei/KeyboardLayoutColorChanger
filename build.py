import os
import shutil
import subprocess
import sys

NAME = 'KeyboardLayoutChanger'
VERSION = '0_0_1'

def clean_build_dirs():
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

def build_exe():
    clean_build_dirs()
    extra_flags = [
            #'--add-data=icon/app.png;icon',  # Bundle icon file into 'icon' subdir in _MEIPASS
            '--add-data=icons;icons',  # Bundle icon file into 'icon' subdir in _MEIPASS
            '--icon=icons/logo/app.png',  # EXE icon (PyInstaller may convert PNG if needed; use ICO for best results)
        ]
    try:
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--onefile', '--noconsole',
            '--name', f'{NAME}-{VERSION}',
            ] + extra_flags + ['main.py' # Your entry script
            # Add flags here, e.g., '--icon=app.ico'
            # If issues with hidden imports (e.g., pystray or 
            # tkinter), add --hidden-import=pystray or similar flags.
        ])
        print("Build successful! EXE in dist/")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
    finally:
        # Optional: Clean build/ but keep dist/
        if os.path.exists('build'):
            shutil.rmtree('build')
        if os.path.exists(f'{NAME}-{VERSION}.spec'):
            os.remove(f'{NAME}-{VERSION}.spec')

if __name__ == '__main__':
    build_exe()