"""
UI Renderer
PlayStation 5 inspired UI for the game launcher using Pygame.
"""

import os
import io
import pygame
import math
import random
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from PIL import Image
    import pillow_avif  # AVIF support
    HAS_PIL = True
except ImportError:
    try:
        from PIL import Image
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False

from game_manager import Game


class Colors:
    """PlayStation-inspired color palette."""
    # Main backgrounds
    BG_DARK = (10, 10, 20)
    BG_GRADIENT_TOP = (15, 15, 35)
    BG_GRADIENT_BOTTOM = (5, 5, 15)

    # PlayStation blue accents
    PS_BLUE = (0, 112, 210)
    PS_BLUE_LIGHT = (45, 145, 255)
    PS_BLUE_GLOW = (0, 150, 255)

    # Tiles and cards
    TILE_BG = (25, 25, 40)
    TILE_HOVER = (35, 35, 55)
    TILE_SELECTED = (45, 45, 70)

    # Text colors
    TEXT_WHITE = (255, 255, 255)
    TEXT_LIGHT = (220, 220, 230)
    TEXT_GRAY = (160, 160, 175)
    TEXT_MUTED = (100, 100, 115)

    # Status colors
    SUCCESS = (0, 200, 130)
    ERROR = (255, 70, 70)
    WARNING = (255, 180, 0)

    # UI elements
    DIVIDER = (50, 50, 70)
    OVERLAY = (0, 0, 0, 220)

    # Selection glow
    GLOW_INNER = (255, 255, 255)
    GLOW_OUTER = (0, 150, 255)


class Particle:
    """Floating background particle for ambient effect."""
    def __init__(self, width: int, height: int):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.uniform(1, 3)
        self.speed = random.uniform(0.2, 0.8)
        self.alpha = random.randint(20, 60)
        self.width = width
        self.height = height

    def update(self):
        self.y -= self.speed
        if self.y < -10:
            self.y = self.height + 10
            self.x = random.randint(0, self.width)

    def draw(self, surface: pygame.Surface):
        particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (*Colors.PS_BLUE_LIGHT, self.alpha),
                          (int(self.size), int(self.size)), int(self.size))
        surface.blit(particle_surf, (int(self.x), int(self.y)))


class UIRenderer:
    """
    PlayStation 5 inspired UI renderer.
    Features gradient backgrounds, glowing selections, and smooth animations.
    """

    def __init__(self, screen: pygame.Surface, config: Dict[str, Any]):
        """Initialize the UI renderer."""
        self.screen = screen
        self.config = config
        self.width, self.height = screen.get_size()

        # UI settings from config
        ui_config = config.get('ui', {})
        self.tile_width = ui_config.get('tile_width', 220)
        self.tile_height = ui_config.get('tile_height', 300)
        self.tile_spacing = ui_config.get('tile_spacing', 25)
        self.scroll_speed = ui_config.get('scroll_speed', 15)

        # Initialize fonts
        self._init_fonts()

        # Load default icon
        self.default_icon = self._create_default_icon()

        # Icon/poster cache
        self.icon_cache: Dict[str, pygame.Surface] = {}

        # Background cache and state
        self.background_cache: Dict[str, pygame.Surface] = {}
        self.current_background: Optional[pygame.Surface] = None
        self.target_background: Optional[pygame.Surface] = None
        self.background_transition = 1.0  # 0 = showing current, 1 = showing target
        self.current_bg_path: Optional[str] = None

        # Animation state
        self.scroll_offset = 0.0
        self.target_scroll_offset = 0.0
        self.selection_animation = 0.0
        self.glow_animation = 0.0

        # Background particles
        self.particles = [Particle(self.width, self.height) for _ in range(30)]

        # Pre-render gradient background
        self.gradient_bg = self._create_gradient_background()

        # Message overlay
        self.message: Optional[str] = None
        self.message_time = 0
        self.message_duration = 3000

    def _init_fonts(self):
        """Initialize PlayStation-style fonts."""
        pygame.font.init()

        # Try modern fonts that look similar to PlayStation
        font_names = ['Segoe UI', 'SF Pro Display', 'Helvetica Neue', 'Arial']
        font_name = None

        for name in font_names:
            if name.lower().replace(' ', '') in [f.lower().replace(' ', '') for f in pygame.font.get_fonts()]:
                font_name = name
                break

        if font_name:
            self.font_title = pygame.font.SysFont(font_name, 56, bold=True)
            self.font_large = pygame.font.SysFont(font_name, 42, bold=True)
            self.font_medium = pygame.font.SysFont(font_name, 28)
            self.font_small = pygame.font.SysFont(font_name, 22)
            self.font_tiny = pygame.font.SysFont(font_name, 16)
        else:
            self.font_title = pygame.font.Font(None, 64)
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 26)
            self.font_tiny = pygame.font.Font(None, 20)

    def _create_gradient_background(self) -> pygame.Surface:
        """Create a vertical gradient background like PS5."""
        surface = pygame.Surface((self.width, self.height))

        for y in range(self.height):
            # Calculate gradient color
            ratio = y / self.height
            r = int(Colors.BG_GRADIENT_TOP[0] + (Colors.BG_GRADIENT_BOTTOM[0] - Colors.BG_GRADIENT_TOP[0]) * ratio)
            g = int(Colors.BG_GRADIENT_TOP[1] + (Colors.BG_GRADIENT_BOTTOM[1] - Colors.BG_GRADIENT_TOP[1]) * ratio)
            b = int(Colors.BG_GRADIENT_TOP[2] + (Colors.BG_GRADIENT_BOTTOM[2] - Colors.BG_GRADIENT_TOP[2]) * ratio)

            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))

        return surface

    def _create_default_icon(self) -> pygame.Surface:
        """Create a PlayStation-style default icon."""
        size = min(self.tile_width - 20, self.tile_height - 60)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Dark background with subtle gradient
        pygame.draw.rect(surface, Colors.TILE_BG, (0, 0, size, size), border_radius=12)

        # PlayStation-style controller icon
        center_x, center_y = size // 2, size // 2

        # Controller body
        body_width = int(size * 0.65)
        body_height = int(size * 0.4)
        body_rect = (center_x - body_width // 2, center_y - body_height // 2, body_width, body_height)
        pygame.draw.ellipse(surface, Colors.TEXT_GRAY, body_rect)
        pygame.draw.ellipse(surface, Colors.TILE_BG,
                           (body_rect[0] + 3, body_rect[1] + 3, body_rect[2] - 6, body_rect[3] - 6))

        # D-pad
        dpad_size = int(size * 0.12)
        dpad_x = center_x - int(size * 0.18)
        pygame.draw.rect(surface, Colors.TEXT_GRAY,
                        (dpad_x - dpad_size // 2, center_y - dpad_size * 1.5, dpad_size, dpad_size * 3),
                        border_radius=2)
        pygame.draw.rect(surface, Colors.TEXT_GRAY,
                        (dpad_x - dpad_size * 1.5, center_y - dpad_size // 2, dpad_size * 3, dpad_size),
                        border_radius=2)

        # Action buttons (small circles)
        btn_x = center_x + int(size * 0.18)
        btn_size = int(size * 0.06)
        for angle in [0, 90, 180, 270]:
            bx = btn_x + int(math.cos(math.radians(angle)) * size * 0.08)
            by = center_y + int(math.sin(math.radians(angle)) * size * 0.08)
            pygame.draw.circle(surface, Colors.TEXT_GRAY, (bx, by), btn_size)

        return surface

    def load_icon(self, icon_path: Optional[str], size: Tuple[int, int] = None) -> pygame.Surface:
        """Load and cache a game icon."""
        if size is None:
            size = (self.tile_width - 20, self.tile_height - 70)

        cache_key = f"{icon_path}_{size[0]}x{size[1]}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        icon = None

        if icon_path and os.path.exists(icon_path):
            try:
                # Use PIL for AVIF and other formats, then convert to pygame
                if HAS_PIL and icon_path.lower().endswith(('.avif', '.webp', '.heic', '.heif')):
                    pil_image = Image.open(icon_path)
                    pil_image = pil_image.convert('RGBA')
                    image_data = pil_image.tobytes()
                    icon = pygame.image.fromstring(image_data, pil_image.size, 'RGBA')
                else:
                    icon = pygame.image.load(icon_path)

                # Scale to fill the tile while maintaining aspect ratio
                icon_rect = icon.get_rect()
                scale = max(size[0] / icon_rect.width, size[1] / icon_rect.height)
                new_size = (max(1, int(icon_rect.width * scale)), max(1, int(icon_rect.height * scale)))
                icon = pygame.transform.smoothscale(icon, new_size)

                # Crop to exact size if needed
                if icon.get_width() >= size[0] and icon.get_height() >= size[1]:
                    crop_rect = pygame.Rect(
                        (icon.get_width() - size[0]) // 2,
                        (icon.get_height() - size[1]) // 2,
                        size[0], size[1]
                    )
                    icon = icon.subsurface(crop_rect).copy()
                else:
                    # If image is smaller, just scale to exact size
                    icon = pygame.transform.smoothscale(icon, size)
            except (pygame.error, ValueError, Exception):
                icon = None

        if icon is None:
            icon = pygame.transform.smoothscale(self.default_icon, size)

        self.icon_cache[cache_key] = icon
        return icon

    def clear_icon_cache(self):
        """Clear the icon cache."""
        self.icon_cache.clear()
        self.background_cache.clear()

    def load_background(self, bg_path: Optional[str]) -> Optional[pygame.Surface]:
        """Load and cache a background image, scaled to screen size with blur effect."""
        if not bg_path or not os.path.exists(bg_path):
            return None

        if bg_path in self.background_cache:
            return self.background_cache[bg_path]

        try:
            # Use PIL for AVIF and other formats
            if HAS_PIL and bg_path.lower().endswith(('.avif', '.webp', '.heic', '.heif')):
                pil_image = Image.open(bg_path)
                pil_image = pil_image.convert('RGBA')
                image_data = pil_image.tobytes()
                bg = pygame.image.fromstring(image_data, pil_image.size, 'RGBA')
            else:
                bg = pygame.image.load(bg_path)

            # Scale to cover the entire screen
            bg_rect = bg.get_rect()
            scale = max(self.width / bg_rect.width, self.height / bg_rect.height)
            new_size = (max(self.width, int(bg_rect.width * scale)),
                       max(self.height, int(bg_rect.height * scale)))
            bg = pygame.transform.smoothscale(bg, new_size)

            # Crop to exact screen size (center crop)
            if bg.get_width() != self.width or bg.get_height() != self.height:
                crop_x = max(0, (bg.get_width() - self.width) // 2)
                crop_y = max(0, (bg.get_height() - self.height) // 2)
                crop_w = min(bg.get_width(), self.width)
                crop_h = min(bg.get_height(), self.height)
                crop_rect = pygame.Rect(crop_x, crop_y, crop_w, crop_h)
                bg = bg.subsurface(crop_rect).copy()

            # If still not exact size, scale to exact screen dimensions
            if bg.get_width() != self.width or bg.get_height() != self.height:
                bg = pygame.transform.smoothscale(bg, (self.width, self.height))

            # Add subtle gradient at bottom for text readability (transparent to semi-dark)
            gradient_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            gradient_height = 250
            for i in range(gradient_height):
                # Gradient from 0 alpha at top to 160 alpha at bottom
                alpha = int(160 * (i / gradient_height) ** 1.5)  # Ease-in curve
                pygame.draw.line(gradient_surface, (0, 0, 0, alpha),
                               (0, self.height - gradient_height + i),
                               (self.width, self.height - gradient_height + i))
            bg.blit(gradient_surface, (0, 0))

            self.background_cache[bg_path] = bg
            return bg
        except pygame.error:
            return None

    def _update_background(self, game: Optional[Game]):
        """Update the background based on selected game."""
        if game is None:
            target_path = None
        else:
            target_path = game.background_path

        # Check if background needs to change
        if target_path != self.current_bg_path:
            self.current_bg_path = target_path
            self.current_background = self.target_background
            self.target_background = self.load_background(target_path)
            self.background_transition = 0.0

        # Animate transition (fast and smooth)
        if self.background_transition < 1.0:
            self.background_transition = min(1.0, self.background_transition + 0.15)

    def _render_background(self):
        """Render the current background with transition effect."""
        # If we have a fully transitioned background, just draw it directly
        if self.target_background and self.background_transition >= 1.0:
            self.screen.blit(self.target_background, (0, 0))
            return

        # Draw gradient as base
        self.screen.blit(self.gradient_bg, (0, 0))

        # Draw current background (fading out)
        if self.current_background and self.background_transition < 1.0:
            bg_copy = self.current_background.copy()
            bg_copy.set_alpha(int(255 * (1.0 - self.background_transition)))
            self.screen.blit(bg_copy, (0, 0))

        # Draw target background (fading in)
        if self.target_background and self.background_transition < 1.0:
            bg_copy = self.target_background.copy()
            bg_copy.set_alpha(int(255 * self.background_transition))
            self.screen.blit(bg_copy, (0, 0))

    def render_main_screen(self, games: List[Game], selected_index: int,
                           controller_connected: bool, button_prompts: Dict[str, str]):
        """Render the PlayStation-style main screen."""
        # Update and render dynamic background
        selected_game = games[selected_index] if games and selected_index < len(games) else None
        self._update_background(selected_game)
        self._render_background()

        # Update and draw particles
        for particle in self.particles:
            particle.update()
            particle.draw(self.screen)

        if not games:
            self._render_no_games_message()
        else:
            self._update_scroll(selected_index, len(games))
            self._render_game_tiles(games, selected_index)
            self._render_game_info_bar(games[selected_index])

        self._render_header(len(games), controller_connected)
        self._render_footer(button_prompts)
        self._render_message()

        # Update animations
        self.selection_animation = (self.selection_animation + 0.08) % (2 * math.pi)
        self.glow_animation = (self.glow_animation + 0.05) % (2 * math.pi)

    def _update_scroll(self, selected_index: int, total_games: int):
        """Update scroll offset for smooth PS5-style scrolling."""
        tile_total_width = self.tile_width + self.tile_spacing

        # Center the selected tile
        center_offset = (self.width - self.tile_width) / 2
        self.target_scroll_offset = center_offset - (selected_index * tile_total_width)

        # Snap to position quickly with minimal easing
        diff = self.target_scroll_offset - self.scroll_offset
        if abs(diff) < 2:
            self.scroll_offset = self.target_scroll_offset
        else:
            self.scroll_offset += diff * 0.4

    def _render_game_tiles(self, games: List[Game], selected_index: int):
        """Render horizontal game tiles like PS5."""
        tile_total_width = self.tile_width + self.tile_spacing
        y_position = (self.height - self.tile_height) // 2 - 40

        for i, game in enumerate(games):
            x_position = int(self.scroll_offset + (i * tile_total_width))

            # Skip if off screen
            if x_position < -self.tile_width - 100 or x_position > self.width + 100:
                continue

            is_selected = (i == selected_index)
            distance_from_center = abs(x_position - (self.width - self.tile_width) / 2)

            self._render_game_tile(game, x_position, y_position, is_selected, distance_from_center)

    def _render_game_tile(self, game: Game, x: int, y: int, is_selected: bool, distance: float):
        """Render a single PS5-style game tile."""
        # Calculate scale and opacity based on selection and distance
        if is_selected:
            scale = 1.1  # Slightly larger when selected, no pulsing
            opacity = 255
        else:
            # Fade out tiles further from center
            fade_start = self.width * 0.3
            fade = max(0, min(1, 1 - (distance - fade_start) / (self.width * 0.4)))
            scale = 0.9 + 0.1 * fade
            opacity = int(120 + 135 * fade)

        scaled_width = int(self.tile_width * scale)
        scaled_height = int(self.tile_height * scale)
        offset_x = (scaled_width - self.tile_width) // 2
        offset_y = (scaled_height - self.tile_height) // 2

        tile_x = x - offset_x
        tile_y = y - offset_y

        # Draw glow effect for selected tile
        if is_selected:
            self._draw_glow(tile_x, tile_y, scaled_width, scaled_height, 100)

        # Load game poster (or fall back to icon) - full tile size
        image_path = game.poster_path or game.icon_path
        poster = self.load_icon(image_path, (scaled_width, scaled_height))

        # Create tile surface with rounded corners
        tile_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)

        # Draw rounded rectangle mask
        pygame.draw.rect(tile_surface, (255, 255, 255, opacity),
                        (0, 0, scaled_width, scaled_height), border_radius=12)

        # Apply poster with mask
        poster.set_alpha(opacity)
        tile_surface.blit(poster, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Draw selection border
        if is_selected:
            pygame.draw.rect(tile_surface, (*Colors.GLOW_INNER, 255),
                           (0, 0, scaled_width, scaled_height),
                           width=3, border_radius=12)

        self.screen.blit(tile_surface, (tile_x, tile_y))

    def _draw_glow(self, x: int, y: int, width: int, height: int, intensity: int):
        """Draw a glowing effect around a rectangle."""
        glow_size = 25
        glow_surface = pygame.Surface((width + glow_size * 2, height + glow_size * 2), pygame.SRCALPHA)

        # Multiple layers of glow
        for i in range(glow_size, 0, -3):
            alpha = int((intensity * (glow_size - i) / glow_size))
            color = (*Colors.PS_BLUE_GLOW, alpha)
            pygame.draw.rect(glow_surface, color,
                           (glow_size - i, glow_size - i, width + i * 2, height + i * 2),
                           border_radius=20 + i)

        self.screen.blit(glow_surface, (x - glow_size, y - glow_size))

    def _render_game_info_bar(self, game: Game):
        """Render PS5-style info bar at bottom."""
        bar_height = 120
        bar_y = self.height - bar_height - 60

        # Semi-transparent bar background
        bar_surface = pygame.Surface((self.width, bar_height), pygame.SRCALPHA)

        # Gradient fade from transparent to semi-opaque
        for i in range(bar_height):
            alpha = int(150 * (i / bar_height))
            pygame.draw.line(bar_surface, (10, 10, 20, alpha), (0, i), (self.width, i))

        self.screen.blit(bar_surface, (0, bar_y))

        # Game title - large and bold
        title_surface = self.font_large.render(game.name, True, Colors.TEXT_WHITE)
        self.screen.blit(title_surface, (60, bar_y + 20))

        # Subtitle info (play count, last played)
        info_parts = []
        if game.play_count > 0:
            info_parts.append(f"Played {game.play_count} time{'s' if game.play_count != 1 else ''}")
        if game.last_played:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(game.last_played)
                info_parts.append(f"Last played {dt.strftime('%B %d, %Y')}")
            except ValueError:
                pass

        if info_parts:
            info_text = "  |  ".join(info_parts)
            info_surface = self.font_small.render(info_text, True, Colors.TEXT_GRAY)
            self.screen.blit(info_surface, (60, bar_y + 70))

    def _render_header(self, game_count: int, controller_connected: bool):
        """Render PS5-style minimal header."""
        # Top gradient overlay for readability
        header_surface = pygame.Surface((self.width, 100), pygame.SRCALPHA)
        for i in range(100):
            alpha = int(100 * (1 - i / 100))
            pygame.draw.line(header_surface, (10, 10, 20, alpha), (0, i), (self.width, i))
        self.screen.blit(header_surface, (0, 0))

        # Library title (left side)
        title = "Game Library"
        title_surface = self.font_medium.render(title, True, Colors.TEXT_WHITE)
        self.screen.blit(title_surface, (40, 35))

        # Game count
        count_surface = self.font_tiny.render(f"{game_count} Games", True, Colors.TEXT_GRAY)
        self.screen.blit(count_surface, (40 + title_surface.get_width() + 20, 42))

        # Controller status (right side) - PS5 style indicator
        if controller_connected:
            status_color = Colors.SUCCESS
            status_text = "Controller Connected"
        else:
            status_color = Colors.TEXT_MUTED
            status_text = "No Controller"

        # Small dot indicator
        pygame.draw.circle(self.screen, status_color,
                          (self.width - 180, 45), 6)
        status_surface = self.font_tiny.render(status_text, True, status_color)
        self.screen.blit(status_surface, (self.width - 165, 38))

    def _render_footer(self, button_prompts: Dict[str, str]):
        """Render PS5-style button prompts footer."""
        footer_y = self.height - 45

        # Define button icons and actions
        prompts = [
            (button_prompts.get('confirm', 'X'), "Select"),
            (button_prompts.get('back', 'O'), "Back"),
            (button_prompts.get('options', 'OPTIONS'), "Options"),
        ]

        # Calculate positions (right-aligned like PS5)
        x = self.width - 40

        for button, action in reversed(prompts):
            # Action text
            action_surface = self.font_tiny.render(action, True, Colors.TEXT_GRAY)
            x -= action_surface.get_width()
            self.screen.blit(action_surface, (x, footer_y))

            # Button icon/text
            x -= 10
            btn_surface = self.font_tiny.render(button, True, Colors.TEXT_WHITE)
            x -= btn_surface.get_width()

            # Draw button background circle/pill
            btn_bg_width = btn_surface.get_width() + 16
            btn_bg_rect = (x - 8, footer_y - 4, btn_bg_width, 26)
            pygame.draw.rect(self.screen, Colors.TILE_BG, btn_bg_rect, border_radius=13)
            pygame.draw.rect(self.screen, Colors.DIVIDER, btn_bg_rect, width=1, border_radius=13)

            self.screen.blit(btn_surface, (x, footer_y))
            x -= 30

    def _render_no_games_message(self):
        """Render PS5-style empty state message."""
        center_y = self.height // 2

        # Icon placeholder
        icon_size = 120
        icon_rect = (self.width // 2 - icon_size // 2, center_y - 120, icon_size, icon_size)
        pygame.draw.rect(self.screen, Colors.TILE_BG, icon_rect, border_radius=20)

        # Folder icon
        pygame.draw.rect(self.screen, Colors.TEXT_MUTED,
                        (icon_rect[0] + 25, icon_rect[1] + 35, icon_size - 50, icon_size - 55),
                        border_radius=8, width=3)
        pygame.draw.rect(self.screen, Colors.TEXT_MUTED,
                        (icon_rect[0] + 25, icon_rect[1] + 30, 35, 15),
                        border_radius=5, width=3)

        # Title
        title_surface = self.font_large.render("No Games Found", True, Colors.TEXT_WHITE)
        title_rect = title_surface.get_rect(centerx=self.width // 2, top=center_y + 20)
        self.screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle = "Go to Options to add game folders"
        sub_surface = self.font_medium.render(subtitle, True, Colors.TEXT_GRAY)
        sub_rect = sub_surface.get_rect(centerx=self.width // 2, top=center_y + 75)
        self.screen.blit(sub_surface, sub_rect)

    def _render_text_with_alpha(self, text: str, x: int, y: int, font: pygame.font.Font,
                                 color: Tuple[int, ...], alpha: int, max_width: int = None,
                                 center: bool = False):
        """Render text with transparency support."""
        if max_width:
            while font.size(text)[0] > max_width and len(text) > 3:
                text = text[:-4] + "..."

        surface = font.render(text, True, color)
        surface.set_alpha(alpha)

        if center:
            rect = surface.get_rect(centerx=x, top=y)
        else:
            rect = surface.get_rect(left=x, top=y)

        self.screen.blit(surface, rect)

    def _render_text_centered(self, text: str, x: int, y: int,
                              font: pygame.font.Font, color: Tuple[int, ...],
                              max_width: int = None):
        """Render text centered at a position."""
        if max_width:
            while font.size(text)[0] > max_width and len(text) > 3:
                text = text[:-4] + "..."

        surface = font.render(text, True, color)
        rect = surface.get_rect(centerx=x, top=y)
        self.screen.blit(surface, rect)

    def show_message(self, message: str, duration: int = 3000):
        """Show a temporary notification message."""
        self.message = message
        self.message_time = pygame.time.get_ticks()
        self.message_duration = duration

    def _render_message(self):
        """Render PS5-style notification toast."""
        if not self.message:
            return

        elapsed = pygame.time.get_ticks() - self.message_time
        if elapsed > self.message_duration:
            self.message = None
            return

        # Animation
        if elapsed < 200:
            # Slide in
            progress = elapsed / 200
            offset_x = int((1 - progress) * 300)
            alpha = int(255 * progress)
        elif elapsed > self.message_duration - 300:
            # Fade out
            progress = (self.message_duration - elapsed) / 300
            offset_x = 0
            alpha = int(255 * progress)
        else:
            offset_x = 0
            alpha = 255

        # Toast container
        padding = 20
        text_surface = self.font_medium.render(self.message, True, Colors.TEXT_WHITE)
        toast_width = text_surface.get_width() + padding * 2
        toast_height = 50

        toast_x = self.width - toast_width - 40 + offset_x
        toast_y = 100

        # Background
        toast_surface = pygame.Surface((toast_width, toast_height), pygame.SRCALPHA)
        pygame.draw.rect(toast_surface, (*Colors.TILE_BG, alpha),
                        (0, 0, toast_width, toast_height), border_radius=10)
        pygame.draw.rect(toast_surface, (*Colors.PS_BLUE, alpha),
                        (0, 0, 4, toast_height), border_radius=2)

        self.screen.blit(toast_surface, (toast_x, toast_y))

        # Text
        text_surface.set_alpha(alpha)
        self.screen.blit(text_surface, (toast_x + padding, toast_y + 12))

    def render_settings_menu(self, settings: Dict[str, Any], selected_option: int,
                             button_prompts: Dict[str, str]):
        """Render PS5-style settings overlay."""
        # Full screen overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))
        self.screen.blit(overlay, (0, 0))

        # Settings panel (right side slide-in style like PS5)
        panel_width = 700
        panel_x = (self.width - panel_width) // 2
        panel_y = 80
        panel_height = self.height - 160

        # Panel background
        pygame.draw.rect(self.screen, Colors.TILE_BG,
                        (panel_x, panel_y, panel_width, panel_height),
                        border_radius=20)

        # Title
        title_surface = self.font_large.render("Settings", True, Colors.TEXT_WHITE)
        self.screen.blit(title_surface, (panel_x + 40, panel_y + 30))

        # Divider
        pygame.draw.line(self.screen, Colors.DIVIDER,
                        (panel_x + 40, panel_y + 90), (panel_x + panel_width - 40, panel_y + 90), 2)

        # Settings options
        options = [
            ("Game Folders", self._format_folders(settings.get('game_folders', [])), "folder"),
            ("Display Mode", "Fullscreen" if settings.get('window', {}).get('fullscreen', False) else "Windowed", "display"),
            ("Sort By", settings.get('sorting', 'alphabetical').title(), "sort"),
            ("Rescan Library", "Search for new games", "refresh"),
            ("Back", "Return to library", "back"),
        ]

        option_y = panel_y + 120
        option_height = 70

        for i, (label, value, icon_type) in enumerate(options):
            is_selected = (i == selected_option)
            option_rect = (panel_x + 20, option_y, panel_width - 40, option_height)

            # Selection highlight
            if is_selected:
                # Glow effect
                glow_surf = pygame.Surface((option_rect[2] + 10, option_rect[3] + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*Colors.PS_BLUE, 40),
                               (0, 0, option_rect[2] + 10, option_rect[3] + 10), border_radius=15)
                self.screen.blit(glow_surf, (option_rect[0] - 5, option_rect[1] - 5))

                pygame.draw.rect(self.screen, Colors.TILE_SELECTED, option_rect, border_radius=12)
                pygame.draw.rect(self.screen, Colors.PS_BLUE, option_rect, width=2, border_radius=12)

            # Label
            label_color = Colors.TEXT_WHITE if is_selected else Colors.TEXT_LIGHT
            label_surface = self.font_medium.render(label, True, label_color)
            self.screen.blit(label_surface, (panel_x + 60, option_y + 12))

            # Value (right aligned)
            if value:
                value_color = Colors.TEXT_GRAY if is_selected else Colors.TEXT_MUTED
                value_surface = self.font_small.render(value, True, value_color)
                value_x = panel_x + panel_width - value_surface.get_width() - 60
                self.screen.blit(value_surface, (value_x, option_y + 24))

            option_y += option_height + 10

        # Footer prompts
        footer_y = panel_y + panel_height - 50
        prompt_text = f"{button_prompts.get('confirm', 'X')} Select    {button_prompts.get('back', 'O')} Back"
        prompt_surface = self.font_small.render(prompt_text, True, Colors.TEXT_GRAY)
        prompt_rect = prompt_surface.get_rect(centerx=self.width // 2, top=footer_y)
        self.screen.blit(prompt_surface, prompt_rect)

    def _format_folders(self, folders: List[str]) -> str:
        """Format folder list for display."""
        if not folders:
            return "Not configured"
        if len(folders) == 1:
            return Path(folders[0]).name
        return f"{len(folders)} folders"

    def render_loading_screen(self, message: str, progress: float = -1):
        """Render PS5-style loading screen."""
        self.screen.blit(self.gradient_bg, (0, 0))

        # Update particles
        for particle in self.particles:
            particle.update()
            particle.draw(self.screen)

        center_x = self.width // 2
        center_y = self.height // 2

        # Loading spinner or progress
        spinner_radius = 40
        spinner_thickness = 4

        if progress < 0:
            # Spinning animation
            angle = (pygame.time.get_ticks() / 5) % 360
            for i in range(12):
                segment_angle = math.radians(angle + i * 30)
                alpha = int(255 * (12 - i) / 12)
                start_r = spinner_radius - 10
                end_r = spinner_radius

                start_x = center_x + int(math.cos(segment_angle) * start_r)
                start_y = center_y - 60 + int(math.sin(segment_angle) * start_r)
                end_x = center_x + int(math.cos(segment_angle) * end_r)
                end_y = center_y - 60 + int(math.sin(segment_angle) * end_r)

                pygame.draw.line(self.screen, (*Colors.PS_BLUE_LIGHT, alpha),
                               (start_x, start_y), (end_x, end_y), spinner_thickness)
        else:
            # Progress ring
            pygame.draw.circle(self.screen, Colors.TILE_BG, (center_x, center_y - 60), spinner_radius, spinner_thickness)

            if progress > 0:
                end_angle = -90 + (360 * progress)
                # Draw progress arc
                for angle in range(int(-90), int(end_angle)):
                    rad = math.radians(angle)
                    x = center_x + int(math.cos(rad) * spinner_radius)
                    y = center_y - 60 + int(math.sin(rad) * spinner_radius)
                    pygame.draw.circle(self.screen, Colors.PS_BLUE_LIGHT, (x, y), spinner_thickness // 2)

        # Loading text
        text_surface = self.font_medium.render(message, True, Colors.TEXT_WHITE)
        text_rect = text_surface.get_rect(center=(center_x, center_y + 20))
        self.screen.blit(text_surface, text_rect)

    def render_error_screen(self, title: str, message: str, button_prompts: Dict[str, str]):
        """Render PS5-style error screen."""
        self.screen.blit(self.gradient_bg, (0, 0))

        center_x = self.width // 2
        center_y = self.height // 2

        # Error icon - triangle with exclamation
        icon_size = 80
        icon_y = center_y - 100

        # Triangle
        points = [
            (center_x, icon_y - 35),
            (center_x - 40, icon_y + 30),
            (center_x + 40, icon_y + 30)
        ]
        pygame.draw.polygon(self.screen, Colors.ERROR, points, width=4)

        # Exclamation
        pygame.draw.line(self.screen, Colors.ERROR,
                        (center_x, icon_y - 10), (center_x, icon_y + 5), 4)
        pygame.draw.circle(self.screen, Colors.ERROR, (center_x, icon_y + 18), 4)

        # Title
        title_surface = self.font_large.render(title, True, Colors.TEXT_WHITE)
        title_rect = title_surface.get_rect(center=(center_x, center_y + 10))
        self.screen.blit(title_surface, title_rect)

        # Message
        msg_surface = self.font_medium.render(message, True, Colors.TEXT_GRAY)
        msg_rect = msg_surface.get_rect(center=(center_x, center_y + 60))
        self.screen.blit(msg_surface, msg_rect)

        # Prompt
        prompt_text = f"Press {button_prompts.get('confirm', 'X')} to continue"
        prompt_surface = self.font_small.render(prompt_text, True, Colors.TEXT_MUTED)
        prompt_rect = prompt_surface.get_rect(center=(center_x, center_y + 130))
        self.screen.blit(prompt_surface, prompt_rect)

    def render_confirmation_dialog(self, title: str, message: str,
                                   button_prompts: Dict[str, str]) -> None:
        """Render PS5-style confirmation dialog."""
        # Darken background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Dialog box
        dialog_width = 500
        dialog_height = 220
        dialog_x = (self.width - dialog_width) // 2
        dialog_y = (self.height - dialog_height) // 2

        # Background with subtle border
        pygame.draw.rect(self.screen, Colors.TILE_BG,
                        (dialog_x, dialog_y, dialog_width, dialog_height),
                        border_radius=16)
        pygame.draw.rect(self.screen, Colors.DIVIDER,
                        (dialog_x, dialog_y, dialog_width, dialog_height),
                        width=1, border_radius=16)

        # Title
        title_surface = self.font_medium.render(title, True, Colors.TEXT_WHITE)
        title_rect = title_surface.get_rect(centerx=self.width // 2, top=dialog_y + 35)
        self.screen.blit(title_surface, title_rect)

        # Message
        msg_surface = self.font_small.render(message, True, Colors.TEXT_GRAY)
        msg_rect = msg_surface.get_rect(centerx=self.width // 2, top=dialog_y + 85)
        self.screen.blit(msg_surface, msg_rect)

        # Button row
        btn_y = dialog_y + dialog_height - 60
        btn_spacing = 140

        # Yes button
        yes_text = f"{button_prompts.get('confirm', 'X')} Yes"
        yes_surface = self.font_small.render(yes_text, True, Colors.TEXT_WHITE)
        yes_rect = (self.width // 2 - btn_spacing - 50, btn_y, 100, 36)
        pygame.draw.rect(self.screen, Colors.PS_BLUE, yes_rect, border_radius=18)
        yes_text_rect = yes_surface.get_rect(center=(yes_rect[0] + 50, yes_rect[1] + 18))
        self.screen.blit(yes_surface, yes_text_rect)

        # No button
        no_text = f"{button_prompts.get('back', 'O')} No"
        no_surface = self.font_small.render(no_text, True, Colors.TEXT_LIGHT)
        no_rect = (self.width // 2 + btn_spacing - 50, btn_y, 100, 36)
        pygame.draw.rect(self.screen, Colors.TILE_HOVER, no_rect, border_radius=18)
        pygame.draw.rect(self.screen, Colors.DIVIDER, no_rect, width=1, border_radius=18)
        no_text_rect = no_surface.get_rect(center=(no_rect[0] + 50, no_rect[1] + 18))
        self.screen.blit(no_surface, no_text_rect)
