"""
Game Launcher Main Class
Coordinates the game manager, controller input, and UI rendering.
"""

import os
import sys
import json
import time
import pygame
import ctypes
from typing import Optional, Dict, Any
from enum import Enum, auto
from pathlib import Path

from controller import InputHandler, InputAction
from game_manager import GameManager, Game
from ui import UIRenderer


class LauncherState(Enum):
    """Enumeration of launcher states."""
    LOADING = auto()
    MAIN_MENU = auto()
    SETTINGS = auto()
    LAUNCHING = auto()
    ERROR = auto()
    CONFIRM_EXIT = auto()


class GameLauncher:
    """
    Main game launcher application.
    Handles the game loop, state management, and coordination between components.
    """

    CONFIG_FILE = "config.json"
    CACHE_FILE = "games_cache.json"

    def __init__(self):
        """Initialize the game launcher."""
        # Load configuration
        self.config = self._load_config()

        # Set SDL environment variables for better controller support
        # These must be set BEFORE pygame.init()
        self._setup_sdl_controller_support()

        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("Game Launcher")

        # Set up display
        self._setup_display()

        # Initialize components
        self.input_handler = InputHandler(self.config.get('controller', {}))
        self.game_manager = GameManager(self.config, self.CACHE_FILE)
        self.ui = UIRenderer(self.screen, self.config)

        # State management
        self.state = LauncherState.LOADING
        self.previous_state = LauncherState.MAIN_MENU
        self.running = True

        # Selection state
        self.selected_index = 0
        self.settings_selected = 0
        self.games = []

        # Error state
        self.error_title = ""
        self.error_message = ""

        # Timing
        self.clock = pygame.time.Clock()
        self.fps = 60

    def _setup_sdl_controller_support(self):
        """
        Configure SDL environment variables for better controller support.
        Must be called before pygame.init().
        """
        # Enable HIDAPI support for PS4/PS5 controllers via USB and Bluetooth
        os.environ['SDL_JOYSTICK_HIDAPI_PS4'] = '1'
        os.environ['SDL_JOYSTICK_HIDAPI_PS5'] = '1'

        # Enable PS4/PS5 rumble support
        os.environ['SDL_JOYSTICK_HIDAPI_PS4_RUMBLE'] = '1'
        os.environ['SDL_JOYSTICK_HIDAPI_PS5_RUMBLE'] = '1'

        # Allow joystick events even when window is not focused
        os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'

        # Enable joystick thread for better responsiveness
        os.environ['SDL_JOYSTICK_THREAD'] = '1'

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        default_config = {
            "game_folders": [],
            "window": {
                "width": 1920,
                "height": 1080,
                "fullscreen": False
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
            "show_recently_played": True,
            "max_recent_games": 10
        }

        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    self._deep_merge(default_config, loaded_config)
                    return default_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")

        return default_config

    def _deep_merge(self, base: dict, overlay: dict):
        """Recursively merge overlay into base dictionary."""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config: {e}")

    def _setup_display(self):
        """Set up the Pygame display."""
        window_config = self.config.get('window', {})
        width = window_config.get('width', 1920)
        height = window_config.get('height', 1080)
        fullscreen = window_config.get('fullscreen', False)

        flags = pygame.DOUBLEBUF | pygame.HWSURFACE

        if fullscreen:
            # Use NOFRAME (borderless window) instead of FULLSCREEN
            # This prevents the window from auto-minimizing when launching games
            flags |= pygame.NOFRAME
            # Use native resolution for fullscreen
            info = pygame.display.Info()
            width = info.current_w
            height = info.current_h
            # Position borderless window at top-left for fullscreen effect
            os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'

        self.screen = pygame.display.set_mode((width, height), flags)

        # Hide mouse cursor for controller-focused UI
        pygame.mouse.set_visible(False)

        # Try to set DPI awareness on Windows
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass

    def run(self):
        """Main application loop."""
        # Initial loading
        self._load_games()

        while self.running:
            # Handle events
            self._handle_events()

            # Update state
            self._update()

            # Render
            self._render()

            # Cap framerate
            self.clock.tick(self.fps)

        self._cleanup()

    def _handle_events(self):
        """Handle Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                # Handle one-shot key events
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()

            elif event.type == pygame.JOYDEVICEADDED:
                # Only show message if we weren't already connected
                was_connected = self.input_handler.get_controller_state().connected
                self.input_handler.check_controller_connection()
                if not was_connected:
                    self.ui.show_message("Controller connected")

            elif event.type == pygame.JOYDEVICEREMOVED:
                # Only show message if we were connected
                was_connected = self.input_handler.get_controller_state().connected
                self.input_handler.check_controller_connection()
                if was_connected:
                    self.ui.show_message("Controller disconnected")

    def _update(self):
        """Update application state."""
        # Get input (controller connection is checked via pygame events)
        action = self.input_handler.get_input()

        # Handle input based on current state
        if self.state == LauncherState.MAIN_MENU:
            self._handle_main_menu_input(action)
        elif self.state == LauncherState.SETTINGS:
            self._handle_settings_input(action)
        elif self.state == LauncherState.ERROR:
            self._handle_error_input(action)
        elif self.state == LauncherState.CONFIRM_EXIT:
            self._handle_confirm_exit_input(action)

    def _handle_main_menu_input(self, action: InputAction):
        """Handle input in the main menu state."""
        if action == InputAction.NONE:
            return

        if action == InputAction.LEFT:
            self.selected_index = max(0, self.selected_index - 1)

        elif action == InputAction.RIGHT:
            self.selected_index = min(len(self.games) - 1, self.selected_index + 1)

        elif action == InputAction.CONFIRM:
            if self.games:
                self._launch_selected_game()

        elif action == InputAction.BACK:
            self.state = LauncherState.CONFIRM_EXIT

        elif action == InputAction.OPTIONS:
            self.state = LauncherState.SETTINGS
            self.settings_selected = 0

        elif action == InputAction.RESCAN:
            self._rescan_games()

    def _handle_settings_input(self, action: InputAction):
        """Handle input in the settings menu."""
        settings_options = 5  # Number of settings options

        if action == InputAction.UP:
            self.settings_selected = (self.settings_selected - 1) % settings_options

        elif action == InputAction.DOWN:
            self.settings_selected = (self.settings_selected + 1) % settings_options

        elif action == InputAction.CONFIRM:
            self._handle_settings_selection()

        elif action == InputAction.BACK:
            self.state = LauncherState.MAIN_MENU

    def _handle_settings_selection(self):
        """Handle selection of a settings option."""
        if self.settings_selected == 0:
            # Game Folders - would open folder selection dialog
            self.ui.show_message("Edit config.json to change game folders")

        elif self.settings_selected == 1:
            # Toggle fullscreen
            self._toggle_fullscreen()

        elif self.settings_selected == 2:
            # Cycle sort order
            sort_options = ['alphabetical', 'recent', 'folder', 'play_count']
            current = self.config.get('sorting', 'alphabetical')
            try:
                current_idx = sort_options.index(current)
                next_idx = (current_idx + 1) % len(sort_options)
            except ValueError:
                next_idx = 0
            self.config['sorting'] = sort_options[next_idx]
            self._save_config()
            self.games = self.game_manager.get_games(self.config['sorting'])
            self.ui.show_message(f"Sort: {self.config['sorting'].title()}")

        elif self.settings_selected == 3:
            # Rescan games
            self.state = LauncherState.MAIN_MENU
            self._rescan_games()

        elif self.settings_selected == 4:
            # Back to main menu
            self.state = LauncherState.MAIN_MENU

    def _handle_error_input(self, action: InputAction):
        """Handle input in the error state."""
        if action == InputAction.CONFIRM or action == InputAction.BACK:
            self.state = self.previous_state

    def _handle_confirm_exit_input(self, action: InputAction):
        """Handle input in the confirm exit dialog."""
        if action == InputAction.CONFIRM:
            self.running = False
        elif action == InputAction.BACK:
            self.state = LauncherState.MAIN_MENU

    def _render(self):
        """Render the current state."""
        button_prompts = self.input_handler.get_button_prompts()

        if self.state == LauncherState.LOADING:
            self.ui.render_loading_screen("Loading Games...", -1)

        elif self.state == LauncherState.MAIN_MENU:
            self.ui.render_main_screen(
                self.games,
                self.selected_index,
                self.input_handler.get_controller_state().connected,
                button_prompts
            )

        elif self.state == LauncherState.SETTINGS:
            # First render main menu in background
            self.ui.render_main_screen(
                self.games,
                self.selected_index,
                self.input_handler.get_controller_state().connected,
                button_prompts
            )
            # Then render settings overlay
            self.ui.render_settings_menu(
                self.config,
                self.settings_selected,
                button_prompts
            )

        elif self.state == LauncherState.LAUNCHING:
            self.ui.render_loading_screen("Launching Game...", -1)

        elif self.state == LauncherState.ERROR:
            self.ui.render_error_screen(self.error_title, self.error_message, button_prompts)

        elif self.state == LauncherState.CONFIRM_EXIT:
            # Render main menu in background
            self.ui.render_main_screen(
                self.games,
                self.selected_index,
                self.input_handler.get_controller_state().connected,
                button_prompts
            )
            # Then render confirmation dialog
            self.ui.render_confirmation_dialog(
                "Exit Launcher?",
                "Are you sure you want to exit?",
                button_prompts
            )

        pygame.display.flip()

    def _load_games(self):
        """Load games from cache or scan."""
        self.state = LauncherState.LOADING
        self._render()
        pygame.display.flip()

        # Try to load from cache first
        if self.game_manager.load_cache():
            self.games = self.game_manager.get_games()
            if self.games:
                self.state = LauncherState.MAIN_MENU
                return

        # No cache or empty - scan for games
        self._rescan_games()

    def _rescan_games(self):
        """Rescan for games in configured folders."""
        self.state = LauncherState.LOADING

        folders = self.config.get('game_folders', [])

        if not folders:
            self.ui.show_message("No game folders configured")
            self.state = LauncherState.MAIN_MENU
            return

        def progress_callback(message: str, progress: float):
            self.ui.render_loading_screen(message, progress)
            pygame.display.flip()
            pygame.event.pump()  # Keep window responsive

        self.games = self.game_manager.scan_games(folders, progress_callback)
        self.selected_index = min(self.selected_index, max(0, len(self.games) - 1))

        # Clear icon cache to reload any changed icons
        self.ui.clear_icon_cache()

        self.state = LauncherState.MAIN_MENU
        self.ui.show_message(f"Found {len(self.games)} games")

    def _launch_selected_game(self):
        """Launch the currently selected game."""
        if not self.games or self.selected_index >= len(self.games):
            return

        game = self.games[self.selected_index]
        self.state = LauncherState.LAUNCHING
        self._render()
        pygame.display.flip()

        # Launch the game
        success, error = self.game_manager.launch_game(game)

        if not success:
            self._show_error("Launch Failed", error)
            return

        self.state = LauncherState.MAIN_MENU

    def _restore_window(self):
        """Restore the launcher window after game exits."""
        # Restore window (platform-specific)
        try:
            if sys.platform == 'win32':
                import win32gui
                import win32con
                hwnd = pygame.display.get_wm_info()['window']
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
        except (ImportError, KeyError):
            pass

        # Ensure display is active
        pygame.display.set_mode(
            self.screen.get_size(),
            self.screen.get_flags()
        )

        # Recheck controller connection
        self.input_handler.check_controller_connection()

    def _toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        current_fullscreen = self.config.get('window', {}).get('fullscreen', False)
        self.config['window']['fullscreen'] = not current_fullscreen
        self._save_config()

        # Re-setup display
        self._setup_display()

        # Recreate UI with new screen
        self.ui = UIRenderer(self.screen, self.config)

        mode = "Fullscreen" if self.config['window']['fullscreen'] else "Windowed"
        self.ui.show_message(f"Mode: {mode}")

    def _show_error(self, title: str, message: str):
        """
        Show an error screen.

        Args:
            title: Error title
            message: Error message
        """
        self.error_title = title
        self.error_message = message
        self.previous_state = self.state
        self.state = LauncherState.ERROR

    def _cleanup(self):
        """Clean up resources before exit."""
        self.input_handler.cleanup()
        pygame.quit()


def main():
    """Entry point for the launcher."""
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    launcher = GameLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
