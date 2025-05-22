import serial

def read_bpm(port='/dev/ttyUSB0', baudrate=9600):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            line = ser.readline().decode().strip()
            return int(line)
    except Exception as e:
        print(f"[WARN] BPM read failed: {e}")
        return None
