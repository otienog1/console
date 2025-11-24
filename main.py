#!/usr/bin/env python3
"""
Game Launcher - Main Entry Point

A PlayStation-style game launcher for PC with controller support.

Usage:
    python main.py [options]

Options:
    --fullscreen    Start in fullscreen mode
    --windowed      Start in windowed mode
    --scan          Force rescan of game folders
    --help          Show this help message
"""

import sys
import os
import argparse


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []

    try:
        import pygame
    except ImportError:
        missing.append("pygame")

    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")

    # win32 is optional but recommended on Windows
    if sys.platform == 'win32':
        try:
            import win32api
        except ImportError:
            print("Warning: pywin32 not installed. Icon extraction will be limited.")
            print("Install with: pip install pywin32")

    if missing:
        print("Error: Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall dependencies with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Game Launcher - A PlayStation-style game launcher for PC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  D-pad/Arrow Keys    Navigate games
  X/Enter             Launch selected game
  Circle/Escape       Exit or go back
  Options/Tab         Open settings
  Triangle/R          Rescan games
  F11                 Toggle fullscreen

Configuration:
  Edit config.json to configure game folders and settings.
        """
    )

    parser.add_argument(
        '--fullscreen', '-f',
        action='store_true',
        help='Start in fullscreen mode'
    )

    parser.add_argument(
        '--windowed', '-w',
        action='store_true',
        help='Start in windowed mode'
    )

    parser.add_argument(
        '--scan', '-s',
        action='store_true',
        help='Force rescan of game folders on startup'
    )

    parser.add_argument(
        '--resolution', '-r',
        type=str,
        metavar='WxH',
        help='Set window resolution (e.g., 1920x1080)'
    )

    parser.add_argument(
        '--add-folder',
        type=str,
        metavar='PATH',
        help='Add a game folder to the configuration'
    )

    parser.add_argument(
        '--list-games',
        action='store_true',
        help='List all detected games and exit'
    )

    return parser.parse_args()


def apply_arguments(args):
    """Apply command line arguments to configuration."""
    import json

    config_file = "config.json"
    config = {}

    # Load existing config
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    modified = False

    # Handle fullscreen/windowed
    if args.fullscreen:
        if 'window' not in config:
            config['window'] = {}
        config['window']['fullscreen'] = True
        modified = True
    elif args.windowed:
        if 'window' not in config:
            config['window'] = {}
        config['window']['fullscreen'] = False
        modified = True

    # Handle resolution
    if args.resolution:
        try:
            width, height = map(int, args.resolution.lower().split('x'))
            if 'window' not in config:
                config['window'] = {}
            config['window']['width'] = width
            config['window']['height'] = height
            modified = True
        except ValueError:
            print(f"Invalid resolution format: {args.resolution}")
            print("Use format: WIDTHxHEIGHT (e.g., 1920x1080)")
            sys.exit(1)

    # Handle add folder
    if args.add_folder:
        folder = os.path.abspath(args.add_folder)
        if os.path.isdir(folder):
            if 'game_folders' not in config:
                config['game_folders'] = []
            if folder not in config['game_folders']:
                config['game_folders'].append(folder)
                print(f"Added game folder: {folder}")
                modified = True
            else:
                print(f"Folder already configured: {folder}")
        else:
            print(f"Folder not found: {folder}")
            sys.exit(1)

    # Save modified config
    if modified:
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config: {e}")

    return args


def list_games():
    """List all detected games and exit."""
    from game_manager import GameManager
    import json

    config_file = "config.json"
    config = {}

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    gm = GameManager(config)

    # Try loading from cache first
    if gm.load_cache():
        games = gm.get_games()
    else:
        folders = config.get('game_folders', [])
        if not folders:
            print("No game folders configured.")
            print("Add folders with: python main.py --add-folder <path>")
            sys.exit(1)

        print("Scanning for games...")
        games = gm.scan_games(folders)

    if not games:
        print("No games found.")
        sys.exit(0)

    print(f"\nFound {len(games)} games:\n")
    print("-" * 60)

    for i, game in enumerate(games, 1):
        print(f"{i:3}. {game.name}")
        print(f"     Path: {game.path}")
        if game.play_count > 0:
            print(f"     Played: {game.play_count} times")
        print()

    print("-" * 60)
    print(f"Total: {len(games)} games")


def main():
    """Main entry point."""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Parse arguments first (before checking deps for --help)
    args = parse_arguments()

    # Handle list-games before importing pygame
    if args.list_games:
        check_dependencies()
        list_games()
        sys.exit(0)

    # Check dependencies
    check_dependencies()

    # Apply command line arguments
    apply_arguments(args)

    # Import and run launcher
    from launcher import GameLauncher

    # Create and run launcher
    launcher = GameLauncher()

    # Force scan if requested
    if args.scan:
        # The launcher will handle this after initialization
        launcher.game_manager.games = []  # Clear cache to force scan

    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\nLauncher interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
