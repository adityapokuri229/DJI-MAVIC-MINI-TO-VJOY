# Known working pings
# 55 0d 04 33 0a 0e 02 00 40 06 27 84 05
# 55 0d 04 33 0a 0e 03 00 40 06 01 f4 4a
# 55 0d 04 33 0a 0e 04 00 40 06 27 1c 3e
# 55 0d 04 33 0a 0e 05 00 40 06 01 6c 71

import serial
import pyvjoy
import argparse
import time
import keyboard

parser = argparse.ArgumentParser(description='Mavic Mini RC <-> VJoy interface.')
parser.add_argument('-p', '--port', help='RC Serial Port', required=True)
parser.add_argument('-d', '--device', help='VJoy Device ID', type=int, default=1)
parser.add_argument('-i', '--invert', help='Invert lv, lh, rv, rh, or cam axis', nargs='*', default=['lv', 'rv'])
parser.add_argument('-b1', '--button1', help='Keyboard Key, For Additional Button', required=True)

args = parser.parse_args()

invert = frozenset(args.invert)

# Maximum value for VJoy to handle (0x8000)
maxValue = 32768

# Reverse-engineered ping data
pingData = bytearray.fromhex('550d04330a0e0300400601f44a')

print("Mavic Mini RC <-> VJoy interface\n")

# Initialize serial and VJoy objects
s = None
j = None

# Open serial
try:
    s = serial.Serial(port=args.port, baudrate=115200)
    print('Opened serial device:', s.name)
except serial.SerialException as e:
    print(f'No Controller Connected could not find port on {args.port}')

# Open VJoy device
try:
    j = pyvjoy.VJoyDevice(args.device)
    print('Opened VJoy device:', j.rID)
except pyvjoy.exceptions.vJoyException as e:
    print('No Controller Connected:', e)

# Check if devices are connected
if s is None or j is None:
    print('\nNo Controller Connected. Press Ctrl+C to exit.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nStopping.')
        exit(0)

# Stylistic: Newline for spacing
print(f'\nPress Ctrl+C (or interrupt) to stop. Press "{args.button1}" to toggle Button 1.\n')

# Process input (min 364, center 1024, max 1684) -> (min 0, center 16384, max 32768)
def parseInput(input, name):
    output = (int.from_bytes(input, byteorder='little') - 364) * 4096 // 165
    if name in invert:
        output = maxValue - output
    return output

# Toggle Button 1 state
button1_state = False  # Initial state: released (False = 0, True = 1)
last_toggle_time = 0  # For debouncing
debounce_delay = 0.2  # 200ms debounce period

def toggle_button():
    global button1_state, last_toggle_time
    current_time = time.time()
    if current_time - last_toggle_time >= debounce_delay:
        button1_state = not button1_state  # Toggle state
        j.set_button(1, 1 if button1_state else 0)  # Set button state
        last_toggle_time = current_time
    return button1_state

try:
    while True:
        # Check for ` key press to toggle button
        if keyboard.is_pressed(args.button1):
            toggle_button()
            while keyboard.is_pressed(args.button1):  # Wait for key release:
                pass

        # Ping device
        s.write(pingData)
        print('\rPinged. ', end='')

        data = s.readline()

        if len(data) == 38:
            # Parse controller input
            left_vertical = parseInput(data[13:15], 'lv')
            left_horizontal = parseInput(data[16:18], 'lh')
            right_vertical = parseInput(data[10:12], 'rv')
            right_horizontal = parseInput(data[7:9], 'rh')
            camera = parseInput(data[19:21], 'cam')

            # Update VJoy input
            j.data.wAxisX = left_horizontal
            j.data.wAxisY = left_vertical
            j.data.wAxisXRot = right_horizontal
            j.data.wAxisYRot = right_vertical
            j.data.wSlider = camera

            # Send VJoy input update
            j.update()

            # Log to console with button state
            button_status = "ON " if button1_state else "OFF"
            print('L: H{0:06d},V{1:06d}; R: H{2:06d},V{3:06d}, CAM: {4:06d}, BTN: {5}'.format(left_horizontal, left_vertical, right_horizontal, right_vertical, camera, button_status), end='')

except serial.SerialException as e:
    print('\n\nCould not read/write:', e)
except KeyboardInterrupt:
    print('\n\nDetected keyboard interrupt.')
finally:
    # Clean up
    if j is not None:
        j.reset()  # Reset vJoy device to clear all inputs
    if s is not None:
        s.close()  # Close serial port
    print('Stopping.')