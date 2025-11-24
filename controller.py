"""
Controller Input Handler
Handles PS4/PS5 controllers and keyboard input for the game launcher.
"""

import pygame
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum, auto


class InputAction(Enum):
    """Enumeration of possible input actions."""
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    CONFIRM = auto()      # X button / Enter
    BACK = auto()         # Circle button / Escape
    OPTIONS = auto()      # Options button / Tab
    RESCAN = auto()       # Triangle button / R
    NONE = auto()


@dataclass
class ControllerState:
    """Represents the current state of the controller."""
    connected: bool = False
    controller_name: str = ""
    battery_level: int = -1  # -1 if unknown


class InputHandler:
    """
    Handles input from PS4/PS5 controllers and keyboard.
    Provides a unified interface for game navigation.
    """

    # PlayStation button mappings (common for PS4/PS5 via DirectInput)
    # These may vary by controller - these are typical mappings
    PS_BUTTON_CROSS = 0       # X button - confirm
    PS_BUTTON_CIRCLE = 1      # Circle - back
    PS_BUTTON_SQUARE = 2      # Square
    PS_BUTTON_TRIANGLE = 3    # Triangle - rescan
    PS_BUTTON_L1 = 4
    PS_BUTTON_R1 = 5
    PS_BUTTON_L2 = 6
    PS_BUTTON_R2 = 7
    PS_BUTTON_SHARE = 8
    PS_BUTTON_OPTIONS = 9     # Options - settings
    PS_BUTTON_L3 = 10
    PS_BUTTON_R3 = 11
    PS_BUTTON_PS = 12
    PS_BUTTON_TOUCHPAD = 13

    # Axis mappings
    PS_AXIS_LEFT_X = 0
    PS_AXIS_LEFT_Y = 1
    PS_AXIS_RIGHT_X = 2
    PS_AXIS_RIGHT_Y = 3
    PS_AXIS_L2 = 4
    PS_AXIS_R2 = 5

    # D-pad hat mapping
    DPAD_HAT = 0

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the input handler.

        Args:
            config: Configuration dictionary with controller settings
        """
        self.config = config
        self.deadzone = config.get('deadzone', 0.3)
        self.repeat_delay = config.get('repeat_delay', 500)  # ms before repeat starts
        self.repeat_interval = config.get('repeat_interval', 150)  # ms between repeats

        self.joystick: Optional[pygame.joystick.JoystickType] = None
        self.state = ControllerState()

        # Input repeat tracking
        self._last_action = InputAction.NONE
        self._action_start_time = 0
        self._last_repeat_time = 0
        self._action_triggered = False

        # Initialize joystick subsystem
        pygame.joystick.init()
        self._connect_controller()

    def _connect_controller(self) -> bool:
        """
        Attempt to connect to a controller.

        Returns:
            True if a controller was connected, False otherwise
        """
        count = pygame.joystick.get_count()

        if count > 0:
            # Try to find a PlayStation controller
            for i in range(count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    name = joystick.get_name().lower()

                    # Check if it's a PlayStation controller
                    if any(ps in name for ps in ['playstation', 'ps4', 'ps5', 'dualshock', 'dualsense', 'wireless controller']):
                        self.joystick = joystick
                        self.state.connected = True
                        self.state.controller_name = joystick.get_name()
                        print(f"Connected to PlayStation controller: {self.state.controller_name}")
                        return True
                except pygame.error:
                    continue

            # If no PlayStation controller found, use the first available
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.state.connected = True
                self.state.controller_name = self.joystick.get_name()
                print(f"Connected to controller: {self.state.controller_name}")
                return True
            except pygame.error:
                pass

        self.state.connected = False
        self.state.controller_name = ""
        return False

    def check_controller_connection(self) -> bool:
        """
        Check and update controller connection status.

        Returns:
            True if a controller is connected
        """
        # Reinitialize joystick subsystem to detect changes
        pygame.joystick.quit()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            if self.state.connected:
                print("Controller disconnected")
                self.joystick = None
                self.state.connected = False
                self.state.controller_name = ""
            return False

        if not self.state.connected:
            return self._connect_controller()

        return True

    def get_input(self) -> InputAction:
        """
        Get the current input action from controller or keyboard.
        Handles input repeat for held directions.

        Returns:
            The current InputAction
        """
        current_time = pygame.time.get_ticks()
        action = self._read_raw_input()

        # Handle input repeat logic
        if action != InputAction.NONE:
            if action != self._last_action:
                # New action - trigger immediately
                self._last_action = action
                self._action_start_time = current_time
                self._last_repeat_time = current_time
                self._action_triggered = True
                return action
            else:
                # Same action held
                if not self._action_triggered:
                    self._action_triggered = True
                    return action

                # Check for repeat
                time_held = current_time - self._action_start_time
                if time_held >= self.repeat_delay:
                    time_since_repeat = current_time - self._last_repeat_time
                    if time_since_repeat >= self.repeat_interval:
                        self._last_repeat_time = current_time
                        return action
        else:
            # No action - reset state
            self._last_action = InputAction.NONE
            self._action_triggered = False

        return InputAction.NONE

    def _read_raw_input(self) -> InputAction:
        """
        Read raw input from controller and keyboard.

        Returns:
            The detected InputAction
        """
        # Check keyboard input first (always available as fallback)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            return InputAction.UP
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            return InputAction.DOWN
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            return InputAction.LEFT
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            return InputAction.RIGHT
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            return InputAction.CONFIRM
        if keys[pygame.K_ESCAPE] or keys[pygame.K_BACKSPACE]:
            return InputAction.BACK
        if keys[pygame.K_TAB] or keys[pygame.K_o]:
            return InputAction.OPTIONS
        if keys[pygame.K_r]:
            return InputAction.RESCAN

        # Check controller input if connected
        if self.joystick and self.state.connected:
            try:
                # Check D-pad (hat)
                if self.joystick.get_numhats() > 0:
                    hat = self.joystick.get_hat(self.DPAD_HAT)
                    if hat[1] == 1:  # Up
                        return InputAction.UP
                    if hat[1] == -1:  # Down
                        return InputAction.DOWN
                    if hat[0] == -1:  # Left
                        return InputAction.LEFT
                    if hat[0] == 1:  # Right
                        return InputAction.RIGHT

                # Check left analog stick
                if self.joystick.get_numaxes() >= 2:
                    axis_x = self.joystick.get_axis(self.PS_AXIS_LEFT_X)
                    axis_y = self.joystick.get_axis(self.PS_AXIS_LEFT_Y)

                    if axis_y < -self.deadzone:
                        return InputAction.UP
                    if axis_y > self.deadzone:
                        return InputAction.DOWN
                    if axis_x < -self.deadzone:
                        return InputAction.LEFT
                    if axis_x > self.deadzone:
                        return InputAction.RIGHT

                # Check buttons
                if self.joystick.get_numbuttons() > 0:
                    if self._is_button_pressed(self.PS_BUTTON_CROSS):
                        return InputAction.CONFIRM
                    if self._is_button_pressed(self.PS_BUTTON_CIRCLE):
                        return InputAction.BACK
                    if self._is_button_pressed(self.PS_BUTTON_OPTIONS):
                        return InputAction.OPTIONS
                    if self._is_button_pressed(self.PS_BUTTON_TRIANGLE):
                        return InputAction.RESCAN

            except pygame.error:
                # Controller may have been disconnected
                self.state.connected = False

        return InputAction.NONE

    def _is_button_pressed(self, button_id: int) -> bool:
        """
        Check if a specific button is pressed.

        Args:
            button_id: The button ID to check

        Returns:
            True if the button is pressed
        """
        try:
            if self.joystick and button_id < self.joystick.get_numbuttons():
                return self.joystick.get_button(button_id)
        except pygame.error:
            pass
        return False

    def wait_for_release(self):
        """Wait for all inputs to be released."""
        while self._read_raw_input() != InputAction.NONE:
            pygame.event.pump()
            pygame.time.wait(10)
        self._last_action = InputAction.NONE
        self._action_triggered = False

    def get_controller_state(self) -> ControllerState:
        """
        Get the current controller state.

        Returns:
            ControllerState object with connection info
        """
        return self.state

    def get_button_prompts(self) -> Dict[str, str]:
        """
        Get the appropriate button prompt labels based on input method.

        Returns:
            Dictionary mapping actions to button labels
        """
        if self.state.connected:
            return {
                'confirm': '✕',
                'back': '○',
                'options': 'OPTIONS',
                'rescan': '△',
                'navigate': 'D-Pad/L-Stick'
            }
        else:
            return {
                'confirm': 'Enter',
                'back': 'Esc',
                'options': 'Tab',
                'rescan': 'R',
                'navigate': 'Arrow Keys'
            }

    def cleanup(self):
        """Clean up controller resources."""
        if self.joystick:
            self.joystick.quit()
        pygame.joystick.quit()


class InputEvent:
    """Represents a single input event for event-based handling."""

    def __init__(self, action: InputAction, source: str = "unknown"):
        self.action = action
        self.source = source  # "controller" or "keyboard"
        self.timestamp = time.time()
