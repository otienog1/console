# Game Launcher Application

Create a game launcher application in Python with the following specifications:

## Project Requirements

**Core Functionality:**

1. Scan a specified folder (and subfolders) on the hard drive for game executables (.exe files, .lnk shortcuts)
2. Display the games in a grid layout with game names and icons/thumbnails
3. Allow users to navigate and select games using PS4/PS5 controllers
4. Launch the selected game when the user presses the action button
5. Return to the launcher after the game is closed

**Technology Stack:**

- Python 3.8+
- Pygame for UI rendering and controller input
- Pillow (PIL) for image handling
- Win32 libraries for icon extraction (if on Windows)

**Controller Support:**

- Support PS4 and PS5 controllers (via DirectInput/XInput)
- Button mapping:
  - D-pad or Left Analog Stick: Navigate through games (up/down/left/right)
  - X button (Cross on PlayStation): Launch selected game
  - Circle button: Exit application or go back
  - Options button: Open settings menu
- Visual button prompts showing PlayStation button symbols
- Handle controller connection/disconnection gracefully

**UI Requirements:**

- Fullscreen or windowed mode (configurable)
- Grid layout showing game tiles (1 row scrolling horizontally)
- Each tile shows:
  - Game icon/thumbnail
  - Game name below icon
- Visual highlight on selected game (border, glow, or color change)
- Smooth scrolling when navigating
- Display button prompts at bottom (e.g., "✕ Launch ○ Exit")
- "10-foot UI" design - large text and icons readable from distance

**Game Detection:**

- Recursively scan user-specified game folder
- Extract game names from executable filenames or folder names
- Extract icons from .exe files
- Cache game list to JSON file for faster subsequent launches
- Allow manual rescan option

**Game Launching:**

- Launch games using subprocess
- Minimize or hide launcher while game is running
- Restore launcher window when game closes
- Handle both .exe and .lnk shortcuts

**Settings/Configuration:**

- Config file (JSON or INI) for:
  - Game folder path(s)
  - Window resolution
  - Controller button mappings (optional)
- Settings menu accessible via controller

**Project Structure:**

```
game_launcher/
├── main.py (entry point)
├── launcher.py (main launcher class)
├── game_manager.py (scan and manage games)
├── controller.py (controller input handling)
├── ui.py (UI rendering)
├── config.json (configuration file)
├── games_cache.json (cached game list)
├── assets/
│   ├── fonts/
│   ├── button_icons/ (PlayStation button symbols)
│   └── default_icon.png
└── requirements.txt
```

**Additional Features:**

- Show game count
- Sort games according to the recently played, alphabetically, or by folder
- Search/filter functionality (optional)
- Recently played section (optional)
- Custom thumbnails support (optional)

**Error Handling:**

- Handle missing game folder gracefully
- Handle controller not connected
- Handle game launch failures
- Display user-friendly error messages

Please create a fully functional application with clean, documented code, proper error handling, and a README.md with setup instructions.

Include configuration for multiple game folders (Steam, Epic Games, GOG, etc.),

and

Add keyboard support as a fallback (arrow keys + Enter/Escape).
