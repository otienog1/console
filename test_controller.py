"""
Controller Detection Test Script
Tests controller detection and button mapping for Bluetooth troubleshooting.
"""

import os
import sys
import pygame
import time

def setup_sdl():
    """Set up SDL environment variables for controller support."""
    os.environ['SDL_JOYSTICK_HIDAPI_PS4'] = '1'
    os.environ['SDL_JOYSTICK_HIDAPI_PS5'] = '1'
    os.environ['SDL_JOYSTICK_HIDAPI_PS4_RUMBLE'] = '1'
    os.environ['SDL_JOYSTICK_HIDAPI_PS5_RUMBLE'] = '1'
    os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'
    os.environ['SDL_JOYSTICK_THREAD'] = '1'
    print("✓ SDL environment variables configured")

def detect_controllers():
    """Detect and display information about all connected controllers."""
    pygame.init()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    print(f"\n{'='*70}")
    print(f"CONTROLLER DETECTION TEST")
    print(f"{'='*70}")
    print(f"\nDetected {count} controller(s)\n")

    if count == 0:
        print("❌ No controllers detected!")
        print("\nTroubleshooting steps:")
        print("1. For USB: Check cable connection (some cables are charge-only)")
        print("2. For Bluetooth:")
        print("   - PS4: Hold PS + Share buttons until light flashes")
        print("   - PS5: Hold PS + Create buttons until light flashes")
        print("   - Pair in Windows Bluetooth settings")
        return None

    controllers = []
    for i in range(count):
        try:
            joystick = pygame.joystick.Joystick(i)
            joystick.init()

            print(f"Controller {i}:")
            print(f"  Name: {joystick.get_name()}")
            print(f"  GUID: {joystick.get_guid()}")
            print(f"  Buttons: {joystick.get_numbuttons()}")
            print(f"  Axes: {joystick.get_numaxes()}")
            print(f"  Hats (D-pads): {joystick.get_numhats()}")

            # Check if it's a PlayStation controller
            name_lower = joystick.get_name().lower()
            ps_identifiers = [
                'playstation', 'ps4', 'ps5', 'dualshock', 'dualsense',
                'wireless controller', 'ps4 controller', 'ps5 controller',
                'sony interactive entertainment', 'sony computer entertainment'
            ]

            is_playstation = any(ps_id in name_lower for ps_id in ps_identifiers)
            print(f"  Detected as: {'✓ PlayStation Controller' if is_playstation else '⚠ Generic Controller'}")

            # Detect likely connection type
            if '09cc' in guid.lower():
                print(f"  Connection: Likely Bluetooth (GUID suggests BT)")
            elif num_buttons == 13:
                print(f"  Connection: Possibly Bluetooth (13 buttons)")
            else:
                print(f"  Connection: Likely USB or varies by driver")

            print()
            controllers.append(joystick)
        except pygame.error as e:
            print(f"❌ Error initializing controller {i}: {e}\n")

    return controllers

def test_buttons(controllers):
    """Test button presses in real-time."""
    if not controllers:
        return

    joystick = controllers[0]
    guid = joystick.get_guid()
    num_buttons = joystick.get_numbuttons()

    print(f"{'='*70}")
    print(f"BUTTON MAPPING TEST - Using Controller: {joystick.get_name()}")
    print(f"{'='*70}")

    # Detect connection type
    if '09cc' in guid.lower() or num_buttons == 13:
        print("\n✓ Bluetooth connection detected!")
        print("  Expected button mappings (Bluetooth):")
        print("  Button 0: Cross (X) - Confirm")
        print("  Button 1: Circle (O) - Back")
        print("  Button 2: Triangle - Rescan")
        print("  Button 3: Square")
        print("  Button 9: Options - Settings")
        print("\nIf these don't match, add this to your config.json controller section:")
        print('  "button_mapping": "bluetooth"')
    else:
        print("\n✓ USB connection detected (or ambiguous)")
        print("  Expected button mappings (USB):")
        print("  Button 0: Cross (X) - Confirm")
        print("  Button 1: Circle (O) - Back")
        print("  Button 2: Square")
        print("  Button 3: Triangle - Rescan")
        print("  Button 9: Options - Settings")
        print("\nIf buttons don't work, add this to your config.json controller section:")
        print('  "button_mapping": "usb"  (or "bluetooth" if using Bluetooth)')

    print("\nPress buttons on your controller (Ctrl+C to exit)...")
    print("-" * 70)

    clock = pygame.time.Clock()
    last_button_state = {}

    try:
        while True:
            pygame.event.pump()

            # Check all buttons
            for btn in range(joystick.get_numbuttons()):
                pressed = joystick.get_button(btn)

                # Only print on state change
                if btn not in last_button_state or last_button_state[btn] != pressed:
                    if pressed:
                        button_name = ""
                        if btn == 0:
                            button_name = "Cross/X (Confirm)"
                        elif btn == 1:
                            button_name = "Circle/O (Back)"
                        elif btn == 2:
                            button_name = "Square"
                        elif btn == 3:
                            button_name = "Triangle (Rescan)"
                        elif btn == 9:
                            button_name = "Options"

                        if button_name:
                            print(f"✓ Button {btn} PRESSED - Expected: {button_name}")
                        else:
                            print(f"  Button {btn} pressed")

                    last_button_state[btn] = pressed

            # Check D-pad (hat)
            if joystick.get_numhats() > 0:
                hat = joystick.get_hat(0)
                if hat != (0, 0):
                    direction = []
                    if hat[0] == -1:
                        direction.append("LEFT")
                    elif hat[0] == 1:
                        direction.append("RIGHT")
                    if hat[1] == 1:
                        direction.append("UP")
                    elif hat[1] == -1:
                        direction.append("DOWN")

                    if 'last_hat' not in locals() or locals()['last_hat'] != hat:
                        print(f"✓ D-Pad: {' + '.join(direction)}")
                        locals()['last_hat'] = hat
                elif 'last_hat' in locals() and locals()['last_hat'] != (0, 0):
                    locals()['last_hat'] = (0, 0)

            # Check analog sticks
            if joystick.get_numaxes() >= 2:
                left_x = joystick.get_axis(0)
                left_y = joystick.get_axis(1)

                if abs(left_x) > 0.5 or abs(left_y) > 0.5:
                    if 'last_stick' not in locals() or (
                        abs(locals()['last_stick'][0] - left_x) > 0.3 or
                        abs(locals()['last_stick'][1] - left_y) > 0.3
                    ):
                        print(f"✓ Left Stick: X={left_x:.2f}, Y={left_y:.2f}")
                        locals()['last_stick'] = (left_x, left_y)

            clock.tick(30)  # 30 FPS

    except KeyboardInterrupt:
        print("\n\nTest completed!")

def main():
    """Main test function."""
    print("PS4/PS5 Controller Detection and Testing Tool")
    print("=" * 70)

    # Setup SDL
    setup_sdl()

    # Detect controllers
    controllers = detect_controllers()

    if controllers:
        print("\n✓ Controller detection successful!")
        print("\nStarting button mapping test...")
        time.sleep(1)
        test_buttons(controllers)
    else:
        print("\n❌ No controllers detected. Please check connection and try again.")

    pygame.quit()

if __name__ == "__main__":
    main()
