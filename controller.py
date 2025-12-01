"""
Controller Input Handler
Handles PS4/PS5 controllers and keyboard input for the game launcher.

Features:
- Enhanced Bluetooth controller detection
- USB and wireless connection support
- Diagnostic logging for troubleshooting
- Fallback support for generic controllers
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

    # PlayStation button mappings - USB (DirectInput mode)
    # These are typical for USB-connected PS4 controllers
    PS_BUTTON_CROSS_USB = 0       # X button - confirm
    PS_BUTTON_CIRCLE_USB = 1      # Circle - back
    PS_BUTTON_SQUARE_USB = 2      # Square
    PS_BUTTON_TRIANGLE_USB = 3    # Triangle - rescan
    PS_BUTTON_L1_USB = 4
    PS_BUTTON_R1_USB = 5
    PS_BUTTON_L2_USB = 6
    PS_BUTTON_R2_USB = 7
    PS_BUTTON_SHARE_USB = 8
    PS_BUTTON_OPTIONS_USB = 9     # Options - settings
    PS_BUTTON_L3_USB = 10
    PS_BUTTON_R3_USB = 11
    PS_BUTTON_PS_USB = 12
    PS_BUTTON_TOUCHPAD_USB = 13

    # PlayStation button mappings - Bluetooth
    # These are typical for Bluetooth-connected PS4 controllers
    # Note: Bluetooth mappings can vary by driver and OS version
    PS_BUTTON_CROSS_BT = 0        # X button - confirm
    PS_BUTTON_CIRCLE_BT = 1       # Circle - back
    PS_BUTTON_SQUARE_BT = 3       # Square
    PS_BUTTON_TRIANGLE_BT = 2     # Triangle - rescan
    PS_BUTTON_L1_BT = 4
    PS_BUTTON_R1_BT = 5
    PS_BUTTON_L2_BT = 6
    PS_BUTTON_R2_BT = 7
    PS_BUTTON_SHARE_BT = 8
    PS_BUTTON_OPTIONS_BT = 9      # Options - settings
    PS_BUTTON_L3_BT = 11
    PS_BUTTON_R3_BT = 12
    PS_BUTTON_PS_BT = 10
    PS_BUTTON_TOUCHPAD_BT = 13

    # Active button mappings (will be set based on detection)
    PS_BUTTON_CROSS = 0
    PS_BUTTON_CIRCLE = 1
    PS_BUTTON_SQUARE = 2
    PS_BUTTON_TRIANGLE = 3
    PS_BUTTON_L1 = 4
    PS_BUTTON_R1 = 5
    PS_BUTTON_L2 = 6
    PS_BUTTON_R2 = 7
    PS_BUTTON_SHARE = 8
    PS_BUTTON_OPTIONS = 9
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
        Only reinitializes if necessary to avoid spurious events.

        Returns:
            True if a controller was connected, False otherwise
        """
        # Only reinitialize if we don't have a joystick and need to detect new ones
        if not self.joystick:
            pygame.joystick.quit()
            pygame.joystick.init()

        count = pygame.joystick.get_count()
        print(f"[Controller] Detected {count} controller(s)")

        if count > 0:
            # Try to find a PlayStation or generic controller
            for i in range(count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    name = joystick.get_name()
                    name_lower = name.lower()

                    # Log detailed controller information
                    print(f"[Controller {i}] Name: {name}")
                    print(f"[Controller {i}] GUID: {joystick.get_guid()}")
                    print(f"[Controller {i}] Buttons: {joystick.get_numbuttons()}")
                    print(f"[Controller {i}] Axes: {joystick.get_numaxes()}")
                    print(f"[Controller {i}] Hats: {joystick.get_numhats()}")

                    # Expanded list of PlayStation controller identifiers
                    # Covers USB, Bluetooth, and various OS/driver combinations
                    ps_identifiers = [
                        'playstation',
                        'ps4', 'ps5',
                        'dualshock', 'dualsense',
                        'wireless controller',
                        'ps4 controller',
                        'ps5 controller',
                        'sony interactive entertainment',
                        'sony computer entertainment',
                        'cuh-zct',  # PS4 controller model numbers
                        'cfI-zct',  # PS5 controller model numbers
                        '054c:05c4',  # PS4 USB vendor:product ID
                        '054c:09cc',  # PS4 Bluetooth vendor:product ID
                        '054c:0ce6',  # PS5 vendor:product ID
                    ]

                    # Check if it's a PlayStation controller
                    if any(ps_id in name_lower for ps_id in ps_identifiers):
                        self.joystick = joystick
                        self.state.connected = True
                        self.state.controller_name = name
                        print(f"[Controller] ✓ Connected to PlayStation controller: {name}")
                        self._detect_button_mapping()
                        self._log_button_test()
                        return True
                except pygame.error as e:
                    print(f"[Controller {i}] Error initializing: {e}")
                    continue

            # If no PlayStation controller found, use the first available
            # This ensures compatibility with Xbox and other generic controllers
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.state.connected = True
                self.state.controller_name = self.joystick.get_name()
                print(f"[Controller] ✓ Connected to generic controller: {self.state.controller_name}")
                self._log_button_test()
                return True
            except pygame.error as e:
                print(f"[Controller] Error connecting to first controller: {e}")

        print("[Controller] No controllers detected")
        self.state.connected = False
        self.state.controller_name = ""
        return False

    def check_controller_connection(self) -> bool:
        """
        Check and update controller connection status.
        Only checks if the joystick instance is still valid, doesn't reinitialize.

        Returns:
            True if a controller is connected
        """
        # Check if we have a valid joystick
        if self.joystick:
            try:
                # Try to get the joystick count to verify it's still valid
                # This doesn't require reinitializing the subsystem
                if pygame.joystick.get_count() > 0:
                    # Verify our joystick is still valid by checking button count
                    self.joystick.get_numbuttons()
                    return True
            except pygame.error:
                # Joystick is no longer valid
                print("Controller disconnected")
                self.joystick = None
                self.state.connected = False
                self.state.controller_name = ""
                return False

        # No joystick or it was invalidated - try to connect
        return self._connect_controller()

    def _detect_button_mapping(self):
        """
        Detect and set the appropriate button mapping scheme.
        Attempts to determine if controller is using USB or Bluetooth mapping.
        """
        if not self.joystick:
            return

        try:
            num_buttons = self.joystick.get_numbuttons()
            guid = self.joystick.get_guid()
            name_lower = self.joystick.get_name().lower()

            # Check for manual override in config
            mapping_mode = self.config.get('button_mapping', None)

            if mapping_mode:
                if mapping_mode.lower() == "bluetooth" or mapping_mode.lower() == "bt":
                    mapping_mode = "Bluetooth"
                    print(f"[Controller] Using Bluetooth mapping (manual config override)")
                elif mapping_mode.lower() == "usb":
                    mapping_mode = "USB"
                    print(f"[Controller] Using USB mapping (manual config override)")
                else:
                    mapping_mode = None  # Invalid config, fall through to auto-detect

            if not mapping_mode:
                # Auto-detection heuristics:
                # Default to USB mapping
                mapping_mode = "USB"

                # Check if GUID suggests Bluetooth (contains '09cc' which is BT product ID)
                if '09cc' in guid.lower():
                    mapping_mode = "Bluetooth"
                    print(f"[Controller] Detected Bluetooth PS4 controller via GUID")
                # Check button count - some Bluetooth controllers report 13 buttons instead of 14
                elif num_buttons == 13:
                    mapping_mode = "Bluetooth"
                    print(f"[Controller] Detected possible Bluetooth mode (13 buttons)")
                # For ambiguous cases, use USB as default but warn user
                else:
                    print(f"[Controller] Using default USB button mapping")
                    print(f"[Controller] If buttons don't work correctly, add '\"button_mapping\": \"bluetooth\"' to config.json")

            # Apply the detected mapping
            if mapping_mode == "Bluetooth":
                self.PS_BUTTON_CROSS = self.PS_BUTTON_CROSS_BT
                self.PS_BUTTON_CIRCLE = self.PS_BUTTON_CIRCLE_BT
                self.PS_BUTTON_SQUARE = self.PS_BUTTON_SQUARE_BT
                self.PS_BUTTON_TRIANGLE = self.PS_BUTTON_TRIANGLE_BT
                self.PS_BUTTON_L1 = self.PS_BUTTON_L1_BT
                self.PS_BUTTON_R1 = self.PS_BUTTON_R1_BT
                self.PS_BUTTON_L2 = self.PS_BUTTON_L2_BT
                self.PS_BUTTON_R2 = self.PS_BUTTON_R2_BT
                self.PS_BUTTON_SHARE = self.PS_BUTTON_SHARE_BT
                self.PS_BUTTON_OPTIONS = self.PS_BUTTON_OPTIONS_BT
                self.PS_BUTTON_L3 = self.PS_BUTTON_L3_BT
                self.PS_BUTTON_R3 = self.PS_BUTTON_R3_BT
                self.PS_BUTTON_PS = self.PS_BUTTON_PS_BT
                self.PS_BUTTON_TOUCHPAD = self.PS_BUTTON_TOUCHPAD_BT
                print(f"[Controller] Applied Bluetooth button mapping")
            else:
                self.PS_BUTTON_CROSS = self.PS_BUTTON_CROSS_USB
                self.PS_BUTTON_CIRCLE = self.PS_BUTTON_CIRCLE_USB
                self.PS_BUTTON_SQUARE = self.PS_BUTTON_SQUARE_USB
                self.PS_BUTTON_TRIANGLE = self.PS_BUTTON_TRIANGLE_USB
                self.PS_BUTTON_L1 = self.PS_BUTTON_L1_USB
                self.PS_BUTTON_R1 = self.PS_BUTTON_R1_USB
                self.PS_BUTTON_L2 = self.PS_BUTTON_L2_USB
                self.PS_BUTTON_R2 = self.PS_BUTTON_R2_USB
                self.PS_BUTTON_SHARE = self.PS_BUTTON_SHARE_USB
                self.PS_BUTTON_OPTIONS = self.PS_BUTTON_OPTIONS_USB
                self.PS_BUTTON_L3 = self.PS_BUTTON_L3_USB
                self.PS_BUTTON_R3 = self.PS_BUTTON_R3_USB
                self.PS_BUTTON_PS = self.PS_BUTTON_PS_USB
                self.PS_BUTTON_TOUCHPAD = self.PS_BUTTON_TOUCHPAD_USB
                print(f"[Controller] Applied USB button mapping")

        except Exception as e:
            print(f"[Controller] Error detecting button mapping: {e}")
            print(f"[Controller] Using default USB mapping")

    def _log_button_test(self):
        """Log a test of button mappings for debugging."""
        if not self.joystick:
            return

        try:
            print(f"[Controller] Button mapping test:")
            print(f"[Controller]   Expected Cross (confirm): Button {self.PS_BUTTON_CROSS}")
            print(f"[Controller]   Expected Circle (back): Button {self.PS_BUTTON_CIRCLE}")
            print(f"[Controller]   Expected Triangle (rescan): Button {self.PS_BUTTON_TRIANGLE}")
            print(f"[Controller]   Expected Options: Button {self.PS_BUTTON_OPTIONS}")
            print(f"[Controller] Press buttons to verify mapping...")
        except Exception as e:
            print(f"[Controller] Error in button test: {e}")

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
        Keyboard input has priority and is checked first.

        Returns:
            The detected InputAction
        """
        # Check keyboard input FIRST - keyboard always takes priority
        # This ensures keyboard works even when controller is connected
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

        # Only check controller input if no keyboard input was detected
        # This prevents controller drift from interfering with keyboard
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
                    # Check for any button press and log for debugging
                    pressed_buttons = []
                    for btn in range(self.joystick.get_numbuttons()):
                        if self.joystick.get_button(btn):
                            pressed_buttons.append(btn)

                    # Log button presses for debugging (only when buttons are pressed)
                    if pressed_buttons and not hasattr(self, '_last_pressed_buttons'):
                        print(f"[Controller] Button(s) pressed: {pressed_buttons}")
                    self._last_pressed_buttons = pressed_buttons if pressed_buttons else []

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
