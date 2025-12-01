# Game Launcher

A PlayStation-style game launcher for PC with full controller support. Navigate and launch your games from your couch using a PS4 or PS5 controller.

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

## Features

- **Controller Support**: Full PS4/PS5 DualShock/DualSense controller support via USB and Bluetooth
  - Enhanced Bluetooth detection and compatibility
  - SDL HIDAPI support for reliable wireless connections
  - Fallback support for generic controllers (Xbox, etc.)
- **Keyboard Fallback**: Arrow keys and Enter/Escape for navigation without a controller
- **10-Foot UI**: Large, readable interface designed for TV/monitor viewing from a distance
- **Multi-Folder Scanning**: Configure multiple game folders (Steam, Epic, GOG, etc.)
- **Icon Extraction**: Automatically extracts icons from game executables
- **Smart Detection**: Intelligently identifies main game executables from folders
- **Game Caching**: Fast startup with cached game list
- **Sorting Options**: Sort alphabetically, by recently played, by folder, or play count
- **Smooth Animations**: Fluid scrolling and selection animations

## Requirements

- Python 3.8 or higher
- Windows 10/11 (for full icon extraction support)
- PS4/PS5 controller (optional - keyboard works as fallback)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment (recommended)**
   ```bash
   cd game_launcher
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate assets** (optional - creates button icons)
   ```bash
   python generate_assets.py
   ```

5. **Configure game folders**

   Edit `config.json` and add your game folders:
   ```json
   {
       "game_folders": [
           "C:/Games",
           "C:/Program Files (x86)/Steam/steamapps/common",
           "C:/Program Files/Epic Games",
           "C:/GOG Games",
           "D:/Games"
       ]
   }
   ```

   Or use the command line:
   ```bash
   python main.py --add-folder "C:/Games"
   ```

6. **Run the launcher**
   ```bash
   python main.py
   ```

## Controls

### PlayStation Controller

| Button | Action |
|--------|--------|
| D-pad / Left Stick | Navigate games |
| ✕ (Cross) | Launch selected game |
| ○ (Circle) | Exit / Go back |
| OPTIONS | Open settings menu |
| △ (Triangle) | Rescan games |

### Keyboard

| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Navigate games |
| Enter / Space | Launch selected game |
| Escape / Backspace | Exit / Go back |
| Tab / O | Open settings menu |
| R | Rescan games |
| F11 | Toggle fullscreen |

## Command Line Options

```bash
python main.py [options]

Options:
  --fullscreen, -f     Start in fullscreen mode
  --windowed, -w       Start in windowed mode
  --scan, -s           Force rescan of game folders on startup
  --resolution WxH     Set window resolution (e.g., 1920x1080)
  --add-folder PATH    Add a game folder to configuration
  --list-games         List all detected games and exit
  --help               Show help message
```

### Examples

```bash
# Start in fullscreen mode
python main.py --fullscreen

# Set custom resolution
python main.py --resolution 2560x1440

# Add a game folder and start
python main.py --add-folder "D:/My Games" --scan

# List all detected games
python main.py --list-games
```

## Configuration

The `config.json` file contains all launcher settings:

```json
{
    "game_folders": [
        "C:/Games",
        "C:/Program Files (x86)/Steam/steamapps/common"
    ],
    "window": {
        "width": 1920,
        "height": 1080,
        "fullscreen": false
    },
    "ui": {
        "tiles_per_row": 7,
        "tile_size": 200,
        "tile_spacing": 30,
        "scroll_speed": 15,
        "highlight_color": [0, 150, 255],
        "background_color": [20, 20, 30],
        "text_color": [255, 255, 255]
    },
    "controller": {
        "deadzone": 0.3,
        "repeat_delay": 500,
        "repeat_interval": 150
    },
    "sorting": "alphabetical",
    "show_recently_played": true,
    "max_recent_games": 10
}
```

### Configuration Options

| Option | Description |
|--------|-------------|
| `game_folders` | List of folder paths to scan for games |
| `window.width` | Window width in pixels |
| `window.height` | Window height in pixels |
| `window.fullscreen` | Start in fullscreen mode |
| `ui.tiles_per_row` | Number of game tiles visible at once |
| `ui.tile_size` | Size of game tiles in pixels |
| `ui.tile_spacing` | Spacing between tiles |
| `ui.highlight_color` | RGB color for selected tile highlight |
| `ui.background_color` | RGB color for background |
| `ui.text_color` | RGB color for text |
| `controller.deadzone` | Analog stick deadzone (0.0-1.0) |
| `controller.repeat_delay` | Delay before input repeat starts (ms) |
| `controller.repeat_interval` | Interval between input repeats (ms) |
| `sorting` | Default sort order: `alphabetical`, `recent`, `folder`, `play_count` |

## Project Structure

```
game_launcher/
├── main.py              # Entry point with CLI argument handling
├── launcher.py          # Main launcher class and game loop
├── game_manager.py      # Game scanning, caching, and launching
├── controller.py        # Controller and keyboard input handling
├── ui.py                # UI rendering with Pygame
├── generate_assets.py   # Asset generation script
├── config.json          # User configuration
├── games_cache.json     # Cached game list (auto-generated)
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── assets/
    ├── default_icon.png
    ├── game_icons/      # Extracted game icons
    └── button_icons/    # PlayStation button icons
```

## Supported Game Sources

The launcher can scan games from:

- **Steam**: `C:/Program Files (x86)/Steam/steamapps/common`
- **Epic Games**: `C:/Program Files/Epic Games`
- **GOG Galaxy**: `C:/GOG Games` or `C:/Program Files (x86)/GOG Galaxy/Games`
- **EA/Origin**: `C:/Program Files/EA Games` or `C:/Program Files (x86)/Origin Games`
- **Ubisoft**: `C:/Program Files (x86)/Ubisoft/Ubisoft Game Launcher/games`
- **Custom folders**: Any folder containing game executables

## Troubleshooting

### Controller not detected

**For USB connections:**
1. Ensure the USB cable is properly connected (some cables are charge-only)
2. Try a different USB port or cable
3. The controller should appear as "Wireless Controller" in Windows Device Manager

**For Bluetooth connections:**
1. **Pairing PS4 Controller:**
   - Hold the PS button + Share button simultaneously until the light bar starts flashing rapidly
   - Open Windows Bluetooth settings → Add Bluetooth or other device → Bluetooth
   - Select "Wireless Controller" when it appears

2. **Pairing PS5 Controller:**
   - Hold the PS button + Create button simultaneously until the light bar starts flashing
   - Follow the same Windows pairing process as PS4

3. **Troubleshooting Bluetooth issues:**
   - Remove the controller from Windows Bluetooth settings and re-pair
   - Ensure no other devices are trying to connect to the controller
   - Check Windows Device Manager for any driver warnings
   - Try running the launcher - it includes enhanced Bluetooth detection with diagnostic logging
   - Check the console output for detailed controller detection information

4. **If Bluetooth still doesn't work:**
   - Some Bluetooth adapters have compatibility issues with PS4/PS5 controllers
   - Try using a different Bluetooth adapter (USB dongles often work better than built-in adapters)
   - As a temporary solution, use a USB cable connection

**Diagnostic logging:**
When you run the launcher, check the console output for detailed information:
- Controller name and GUID
- Number of buttons, axes, and hats detected
- Button press detection (press buttons to see which numbers are triggered)

This information can help identify button mapping issues.

### Games not found

1. Check that the game folders in `config.json` are correct
2. Press Triangle (or R) to rescan games
3. Run with `--list-games` to see what games are detected
4. Check the console output for any error messages

### Icons not showing

1. Ensure you have `pywin32` installed: `pip install pywin32`
2. Run `python generate_assets.py` to create default icons
3. Some executables may not have extractable icons

### Performance issues

1. Reduce `ui.tiles_per_row` in config for slower systems
2. Reduce `ui.tile_size` for faster rendering
3. Use windowed mode instead of fullscreen

## Building an Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "GameLauncher" main.py
```

The executable will be in the `dist` folder.

## License

This project is provided as-is for personal use.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Icon extraction using [pywin32](https://github.com/mhammond/pywin32)
- Image processing with [Pillow](https://python-pillow.org/)
