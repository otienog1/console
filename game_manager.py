"""
Game Manager
Handles scanning for games, extracting icons, and managing the game cache.
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import pygame

try:
    import win32api
    import win32con
    import win32gui
    import win32ui
    from PIL import Image
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("Warning: win32 libraries not available. Icon extraction will be limited.")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class Game:
    """Represents a detected game."""
    name: str
    path: str
    icon_path: Optional[str] = None
    poster_path: Optional[str] = None
    background_path: Optional[str] = None
    folder_source: str = ""
    last_played: Optional[str] = None
    play_count: int = 0
    is_shortcut: bool = False
    hash_id: str = ""

    def __post_init__(self):
        if not self.hash_id:
            self.hash_id = hashlib.md5(self.path.encode()).hexdigest()[:12]
        # Auto-detect poster and background from images_ folder
        self._detect_images()

    def _detect_images(self):
        """Detect poster and background images from the images_ folder."""
        if not self.path:
            return

        game_dir = os.path.dirname(self.path)
        images_folder = os.path.join(game_dir, "images_")

        if os.path.exists(images_folder):
            # Supported image extensions (including AVIF)
            image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.avif', '.heic', '.heif']

            # Look for poster image
            for ext in image_extensions:
                poster_file = os.path.join(images_folder, f"poster{ext}")
                if os.path.exists(poster_file):
                    self.poster_path = poster_file
                    break

            # Look for background image
            for ext in image_extensions:
                bg_file = os.path.join(images_folder, f"background{ext}")
                if os.path.exists(bg_file):
                    self.background_path = bg_file
                    break

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Game':
        """Create a Game instance from a dictionary."""
        return cls(**data)


class GameManager:
    """
    Manages game detection, icon extraction, and caching.
    """

    # Common executable patterns to ignore (launchers, updaters, etc.)
    IGNORED_PATTERNS = [
        'unins', 'uninst', 'uninstall', 'setup', 'install', 'config',
        'crash', 'report', 'update', 'patch', 'launcher', 'bootstrap',
        'redist', 'vcredist', 'directx', 'dotnet', 'ue4prereq',
        'easyanticheat', 'battleye', 'dxsetup', 'physx', '_CommonRedist',
        'support', 'cleanup', 'diagnostic', 'repair', 'verify'
    ]

    # Common game executable patterns (prioritize these)
    GAME_PATTERNS = [
        'game', 'play', 'start', 'launch', 'run', 'main', 'win64', 'win32'
    ]

    def __init__(self, config: Dict[str, Any], cache_path: str = "games_cache.json"):
        """
        Initialize the game manager.

        Args:
            config: Configuration dictionary
            cache_path: Path to the cache file
        """
        self.config = config
        self.cache_path = cache_path
        self.games: List[Game] = []
        self.icons_dir = Path("assets/game_icons")
        self.icons_dir.mkdir(parents=True, exist_ok=True)

    def load_cache(self) -> bool:
        """
        Load games from cache file.

        Returns:
            True if cache was loaded successfully
        """
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.games = [Game.from_dict(g) for g in data.get('games', [])]
                    print(f"Loaded {len(self.games)} games from cache")
                    return True
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error loading cache: {e}")

        return False

    def save_cache(self):
        """Save games to cache file."""
        try:
            data = {
                'version': '1.0',
                'last_scan': datetime.now().isoformat(),
                'games': [g.to_dict() for g in self.games]
            }
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.games)} games to cache")
        except IOError as e:
            print(f"Error saving cache: {e}")

    def scan_games(self, folders: List[str], progress_callback: Optional[callable] = None) -> List[Game]:
        """
        Scan folders for game executables.

        Args:
            folders: List of folder paths to scan
            progress_callback: Optional callback for progress updates (message, progress 0-1)

        Returns:
            List of detected games
        """
        self.games = []
        found_paths = set()
        total_folders = len([f for f in folders if os.path.exists(f)])
        scanned = 0

        for folder in folders:
            if not os.path.exists(folder):
                print(f"Folder not found: {folder}")
                continue

            if progress_callback:
                progress_callback(f"Scanning: {folder}", scanned / max(total_folders, 1))

            games_in_folder = self._scan_folder(folder, found_paths)
            self.games.extend(games_in_folder)
            scanned += 1

        # Sort and save
        self._sort_games()
        self.save_cache()

        if progress_callback:
            progress_callback(f"Found {len(self.games)} games", 1.0)

        return self.games

    def _scan_folder(self, folder: str, found_paths: set) -> List[Game]:
        """
        Recursively scan a folder for games.

        Args:
            folder: Folder path to scan
            found_paths: Set of already found paths to avoid duplicates

        Returns:
            List of games found in this folder
        """
        games = []
        folder_path = Path(folder)

        try:
            # First, look for .lnk shortcuts
            for lnk_file in folder_path.glob("*.lnk"):
                target = self._resolve_shortcut(str(lnk_file))
                if target and target.lower().endswith('.exe') and target not in found_paths:
                    if not self._should_ignore(target):
                        found_paths.add(target)
                        game = self._create_game_entry(target, folder, is_shortcut=True)
                        if game:
                            games.append(game)

            # Scan subdirectories (typically each game is in its own folder)
            for item in folder_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Look for main game executable in this subfolder
                    game = self._find_game_in_folder(item, folder, found_paths)
                    if game:
                        games.append(game)

            # Also check for executables directly in this folder
            for exe_file in folder_path.glob("*.exe"):
                if str(exe_file) not in found_paths and not self._should_ignore(str(exe_file)):
                    found_paths.add(str(exe_file))
                    game = self._create_game_entry(str(exe_file), folder)
                    if game:
                        games.append(game)

        except PermissionError:
            print(f"Permission denied: {folder}")
        except Exception as e:
            print(f"Error scanning {folder}: {e}")

        return games

    def _find_game_in_folder(self, game_folder: Path, source_folder: str, found_paths: set) -> Optional[Game]:
        """
        Find the main game executable in a game folder.

        Args:
            game_folder: Path to the game's folder
            source_folder: The source folder being scanned
            found_paths: Set of already found paths

        Returns:
            Game object or None
        """
        exe_files = []

        try:
            # Get all .exe files recursively (but not too deep)
            for exe in game_folder.rglob("*.exe"):
                # Limit depth
                rel_path = exe.relative_to(game_folder)
                if len(rel_path.parts) <= 3:  # Max 3 levels deep
                    if not self._should_ignore(str(exe)):
                        exe_files.append(exe)
        except PermissionError:
            return None

        if not exe_files:
            return None

        # Score and sort executables to find the most likely game executable
        scored_exes = []
        for exe in exe_files:
            score = self._score_executable(exe, game_folder.name)
            scored_exes.append((exe, score))

        scored_exes.sort(key=lambda x: x[1], reverse=True)

        # Take the highest scored executable
        best_exe = scored_exes[0][0]
        exe_path = str(best_exe)

        if exe_path in found_paths:
            return None

        found_paths.add(exe_path)
        return self._create_game_entry(exe_path, source_folder, folder_name=game_folder.name)

    def _score_executable(self, exe_path: Path, folder_name: str) -> int:
        """
        Score an executable to determine if it's likely the main game.

        Args:
            exe_path: Path to the executable
            folder_name: Name of the game folder

        Returns:
            Score (higher is better)
        """
        score = 0
        name_lower = exe_path.stem.lower()
        folder_lower = folder_name.lower()

        # Bonus if name matches folder name
        if name_lower in folder_lower or folder_lower in name_lower:
            score += 50

        # Bonus for being in root or bin folder
        rel_parts = exe_path.parts
        if len(rel_parts) <= 2:
            score += 20
        if 'bin' in str(exe_path).lower() or 'binaries' in str(exe_path).lower():
            score += 15

        # Bonus for game-related patterns
        for pattern in self.GAME_PATTERNS:
            if pattern in name_lower:
                score += 10

        # Bonus for larger file size (games are usually larger)
        try:
            size = exe_path.stat().st_size
            if size > 50 * 1024 * 1024:  # > 50MB
                score += 30
            elif size > 10 * 1024 * 1024:  # > 10MB
                score += 20
            elif size > 1 * 1024 * 1024:  # > 1MB
                score += 10
        except OSError:
            pass

        # Penalty for common non-game patterns
        for pattern in self.IGNORED_PATTERNS:
            if pattern in name_lower:
                score -= 100

        return score

    def _should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: Path to check

        Returns:
            True if should be ignored
        """
        name_lower = Path(path).stem.lower()
        path_lower = path.lower()

        for pattern in self.IGNORED_PATTERNS:
            if pattern in name_lower or pattern in path_lower:
                return True

        return False

    def _create_game_entry(self, exe_path: str, source_folder: str,
                           folder_name: Optional[str] = None, is_shortcut: bool = False) -> Optional[Game]:
        """
        Create a game entry from an executable path.

        Args:
            exe_path: Path to the executable
            source_folder: Source folder being scanned
            folder_name: Optional folder name to use for game name
            is_shortcut: Whether this came from a shortcut

        Returns:
            Game object or None
        """
        try:
            # Determine game name
            if folder_name:
                name = self._clean_game_name(folder_name)
            else:
                name = self._clean_game_name(Path(exe_path).stem)

            # Extract icon
            icon_path = self._extract_icon(exe_path)

            return Game(
                name=name,
                path=exe_path,
                icon_path=icon_path,
                folder_source=source_folder,
                is_shortcut=is_shortcut
            )
        except Exception as e:
            print(f"Error creating game entry for {exe_path}: {e}")
            return None

    def _clean_game_name(self, name: str) -> str:
        """
        Clean up a game name for display.

        Args:
            name: Raw name

        Returns:
            Cleaned name
        """
        # Remove common suffixes
        suffixes = ['-Win64-Shipping', '-Win32-Shipping', '_x64', '_x86', '-x64', '-x86',
                    '_64', '_32', ' x64', ' x86', 'Win64', 'Win32']
        for suffix in suffixes:
            if name.lower().endswith(suffix.lower()):
                name = name[:-len(suffix)]

        # Replace underscores and dashes with spaces
        name = name.replace('_', ' ').replace('-', ' ')

        # Remove multiple spaces
        while '  ' in name:
            name = name.replace('  ', ' ')

        return name.strip()

    def _resolve_shortcut(self, lnk_path: str) -> Optional[str]:
        """
        Resolve a Windows shortcut to its target.

        Args:
            lnk_path: Path to the .lnk file

        Returns:
            Target path or None
        """
        if not HAS_WIN32:
            return None

        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            return shortcut.Targetpath
        except Exception:
            return None

    def _extract_icon(self, exe_path: str) -> Optional[str]:
        """
        Extract icon from an executable file.

        Args:
            exe_path: Path to the executable

        Returns:
            Path to saved icon or None
        """
        if not HAS_WIN32 or not HAS_PIL:
            return None

        try:
            # Generate unique filename for this icon
            icon_hash = hashlib.md5(exe_path.encode()).hexdigest()[:12]
            icon_filename = f"{icon_hash}.png"
            icon_path = self.icons_dir / icon_filename

            # Check if already extracted
            if icon_path.exists():
                return str(icon_path)

            # Extract icon using win32
            large_icons, small_icons = win32gui.ExtractIconEx(exe_path, 0, 1, 1)

            if large_icons:
                icon_handle = large_icons[0]

                # Create device context
                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, 256, 256)
                hdc_mem = hdc.CreateCompatibleDC()
                hdc_mem.SelectObject(hbmp)

                # Draw icon
                win32gui.DrawIconEx(hdc_mem.GetHandleOutput(), 0, 0, icon_handle,
                                    256, 256, 0, None, win32con.DI_NORMAL)

                # Convert to PIL Image
                bmpinfo = hbmp.GetInfo()
                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer('RGBA', (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                                       bmpstr, 'raw', 'BGRA', 0, 1)

                # Save icon
                img.save(str(icon_path), 'PNG')

                # Cleanup
                win32gui.DestroyIcon(icon_handle)
                hdc_mem.DeleteDC()
                hdc.DeleteDC()

                return str(icon_path)

            # Cleanup any extracted icons
            for icon in large_icons + small_icons:
                win32gui.DestroyIcon(icon)

        except Exception as e:
            # Silently fail - we'll use default icon
            pass

        return None

    def _sort_games(self):
        """Sort games based on configuration."""
        sort_method = self.config.get('sorting', 'alphabetical')

        if sort_method == 'alphabetical':
            self.games.sort(key=lambda g: g.name.lower())
        elif sort_method == 'recent':
            self.games.sort(key=lambda g: g.last_played or '', reverse=True)
        elif sort_method == 'folder':
            self.games.sort(key=lambda g: (g.folder_source, g.name.lower()))
        elif sort_method == 'play_count':
            self.games.sort(key=lambda g: g.play_count, reverse=True)

    def get_games(self, sort_by: Optional[str] = None) -> List[Game]:
        """
        Get the list of games, optionally sorted.

        Args:
            sort_by: Optional sort method override

        Returns:
            List of games
        """
        if sort_by:
            original_sort = self.config.get('sorting')
            self.config['sorting'] = sort_by
            self._sort_games()
            self.config['sorting'] = original_sort

        return self.games

    def get_recent_games(self, max_count: int = 10) -> List[Game]:
        """
        Get recently played games.

        Args:
            max_count: Maximum number of recent games

        Returns:
            List of recently played games
        """
        recent = [g for g in self.games if g.last_played]
        recent.sort(key=lambda g: g.last_played or '', reverse=True)
        return recent[:max_count]

    def update_game_played(self, game: Game):
        """
        Update a game's play statistics.

        Args:
            game: The game that was played
        """
        game.last_played = datetime.now().isoformat()
        game.play_count += 1
        self.save_cache()

    def search_games(self, query: str) -> List[Game]:
        """
        Search for games by name.

        Args:
            query: Search query

        Returns:
            List of matching games
        """
        query_lower = query.lower()
        return [g for g in self.games if query_lower in g.name.lower()]

    def get_game_count(self) -> int:
        """Get total number of games."""
        return len(self.games)

    def launch_game(self, game: Game) -> Tuple[bool, str]:
        """
        Launch a game.

        Args:
            game: The game to launch

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not os.path.exists(game.path):
                return False, f"Game not found: {game.path}"

            # Update play statistics
            self.update_game_played(game)

            # Launch the game using os.startfile which properly activates the window
            # This works for both .exe files and .lnk shortcuts
            os.startfile(game.path)

            return True, ""

        except PermissionError:
            return False, "Permission denied. Try running as administrator."
        except FileNotFoundError:
            return False, f"Game executable not found: {game.path}"
        except Exception as e:
            return False, f"Failed to launch game: {str(e)}"
