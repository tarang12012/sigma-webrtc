import serial

ser = serial.Serial('/dev/ttyUSB0', 115200)


def send_2():
    ser.write(b'2\n')
    print("Sent 2")


def send_4():
    ser.write(b'4\n')
    print("Sent 4")


def send_6():
    ser.write(b'6\n')
    print("Sent 6")


def send_8():
    ser.write(b'8\n')
    print("Sent 8")


def send_5():
    ser.write(b'5\n')
    print("Sent 5")
