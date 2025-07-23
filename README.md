# Keyboard Layout Color Changer

## Description

This is a lightweight Windows application that automatically changes your desktop background color based on the current keyboard layout. It helps users who frequently switch between layouts (e.g., English and Norwegian) by providing a visual cue—different colors for different layouts—to avoid typing errors without constantly checking the taskbar.

The app runs in the background with a system tray icon for easy toggling (on/off) and settings to customize colors and flag icons per layout. It's designed to be slim, with low CPU usage, making it suitable for always-on operation.

Key goals: Clean, concise Python code with low technical debt and entanglement, serving as a PoC/MVP that's easy to expand.

## Features

- **Automatic Detection**: Monitors keyboard layout changes in real-time and updates the desktop wallpaper to a solid color associated with the layout.
- **System Tray Icon**: 
  - Toggle monitoring on/off.
  - Access settings to customize colors and flags for each installed layout.
  - Displays the current layout's flag icon (or a default logo when off).
- **Settings UI**: A simple Tkinter window to select colors (via color picker) and flags (from bundled icons) for each layout. Changes are applied only after saving.
- **Lightweight**: Uses minimal resources; polling interval adjusts dynamically (0.1s when active, 1s when off).
- **Bundled Icons**: Includes flag icons for countries/languages and app logos.
- **EXE Support**: Can be built into a single-file executable for easy distribution and startup integration.

## Installation

### Prerequisites
- Windows OS (tested on Windows 10/11).
- Python 3.10+ (for running from source).
- Install dependencies from `requirements.txt`:
  ```
  pip install -r requirements.txt
  ```

### From Source
Clone the repository and run `main.py`:
```
git clone <repo-url>
cd <repo-dir>
pip install -r requirements.txt
python main.py
```

### As Executable
Use the provided build script (`build.py`) to create a standalone `.exe`:
1. Ensure PyInstaller is installed: `pip install pyinstaller`.
2. Run `python build.py`.
3. The EXE will be in the `dist/` folder (e.g., `KeyboardLayoutChanger-0_0_1.exe`).

## Usage

1. Run the EXE or `main.py`.
2. The app starts in the system tray (look for the logo or flag icon).
3. Switch keyboard layouts (e.g., Alt+Shift) to see the wallpaper change.
4. Right-click the tray icon:
   - **Toggle On/Off**: Enable/disable monitoring (restores original wallpaper when off).
   - **Settings**: Open the UI to customize colors and flags.
   - **Quit**: Exit the app.
5. In Settings:
   - View detected layouts with current color, hex code, and flag (with country code).
   - Click the color button to pick a new hex color.
   - Click the flag button to select from available country flags.
   - Save changes to apply; Cancel to discard.

Data is stored in `~/.keyboard_layout_colors/` (config JSON and generated images).

### Making the Tray Icon Visible on the Taskbar
By default, the app's tray icon may appear under "hidden icons" (the upward arrow in the system tray). To make it permanently visible on the taskbar:
- Drag and drop the icon from the hidden icons area to the main taskbar.
- Alternatively, customize taskbar icons via Windows settings: Go to Settings > Personalization > Taskbar > Select which icons appear on the taskbar (or search for "taskbar settings"). Enable the toggle for "Keyboard Layout Color Changer".
For more details: [Customize the taskbar in Windows](https://support.microsoft.com/en-us/windows/customize-the-taskbar-in-windows-0657a50f-0cc7-dbfd-ae6b-05020b195b07).

## Configuration

- **Colors**: Defaults to a palette of 10 hex colors; customizable per layout.
- **Flags**: Defaults to country codes from Windows locale info; select from bundled PNGs in `icons/flags/`.
- **Logs**: Check `~/.keyboard_layout_colors/app.log` for debugging.

## Running at Startup

To have the app launch automatically on Windows boot (so it runs in the background after restarts):

1. Open the Run dialog: Press `Win + R`.
2. Type `shell:startup` and press Enter. This opens the Startup folder (e.g., `C:\Users\YourUsername\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`).
3. Create a shortcut to the EXE:
   - Right-click in the folder > New > Shortcut.
   - Browse to your EXE (e.g., `dist\KeyboardLayoutChanger-0_0_1.exe`).
   - Name it (e.g., "Keyboard Layout Color Changer").
4. The app will now start automatically on login.

Alternatively, use Task Scheduler for more control:
1. Search for "Task Scheduler" in the Start menu.
2. Create a new task: Action > Create Task.
3. General: Name it, check "Run with highest privileges".
4. Triggers: New > At log on > OK.
5. Actions: New > Start a program > Browse to EXE > OK.
6. Conditions: Uncheck "Start only if on AC power" if needed.
7. Save the task.

## Building the EXE

The project includes a `build.py` script for creating a standalone executable using PyInstaller.

- Run `python build.py`.
- Customizes: Bundles `icons/` directory (flags and logos), sets EXE icon.
- Output: Single-file EXE in `dist/`.

Note: If building fails (e.g., missing imports), add `--hidden-import` flags for modules like `tkinter` or `pystray`.

## Credits

- Flag icons are sourced from [emcrisostomo/flags](https://github.com/emcrisostomo/flags/tree/master). Thank you to the contributors for providing these high-quality icons.

## License

MIT License

Copyright (c) [Your Year] [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Contributing

Feel free to fork and submit PRs for improvements, such as adding support for more layouts or features like notifications. Issues welcome!