import board
import busio
import digitalio
import time
import sdcardio
import storage
import adafruit_sdcard
import adafruit_rfm9x
import adafruit_character_lcd.character_lcd_i2c as character_lcd
from adafruit_debouncer import Debouncer
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from lcd.lcd import CursorMode
import adafruit_gps

# Set up modules and buttons
#Lora setup

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
#SDcard setup
cs_s = board.A0
sdcard = sdcardio.SDCard(spi, cs_s)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs,"/sd")
#time.sleep(3)
# Initialze RFM radio
RADIO_FREQ_MHZ = 433.0  # Frequency of the radio in Mhz. Must match your
CS_R = digitalio.DigitalInOut(board.D11)
RESET_R = digitalio.DigitalInOut(board.A1)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS_R, RESET_R, RADIO_FREQ_MHZ)
rfm9x.tx_power = 23
#LCD screen Setup
lcd = LCD(I2CPCF8574Interface(board.I2C(), 0x27), num_rows=4, num_cols=20)

#GPS SETUP
uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
# Create a GPS module instance.
gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial
# Turn on the basic GGA and RMC info (what you typically want)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")
last_print = time.monotonic()


#Buttons setup
pin_1 = digitalio.DigitalInOut(board.D9)
pin_1.direction = digitalio.Direction.INPUT
pin_1.pull = digitalio.Pull.UP
btn_1 = Debouncer(pin_1)

pin_2 = digitalio.DigitalInOut(board.D6)
pin_2.direction = digitalio.Direction.INPUT
pin_2.pull = digitalio.Pull.UP
btn_2 = Debouncer(pin_2)

pin_3 = digitalio.DigitalInOut(board.D5)
pin_3.direction = digitalio.Direction.INPUT
pin_3.pull = digitalio.Pull.UP
btn_3 = Debouncer(pin_3)

pin_4 = digitalio.DigitalInOut(board.D4)
pin_4.direction = digitalio.Direction.INPUT
pin_4.pull = digitalio.Pull.UP
btn_4 = Debouncer(pin_4)

#dict setup
alphabet = {'A': '.-','B': '-...','C': '-.-.','D': '-..',
            'E': '.','F': '..-.','G': '--.','H': '....',
            'I': '..','J': '.---','K': '-.-','L': '.-..',
            'M': '--','N': '-.','O': '---','P': '.--.',
            'Q': '--.-','R': '.-.','S': '...','T': '-',
            'U': '..-','V': '...-','W': '.--','X': '-..-',
            'Y': '-.--','Z': '--..','1': '.----','2': '..---',
            '3': '...--','4': '....-','5': '.....','6': '-....',
            '7': '--...','8': '---..','9': '----.','0': '-----',
            ', ': '--..--','.': '.-.-.-','?': '..--..','/': '-..-.',
            '-': '-....-','(': '-.--.',')': '-.--.-'}

#functions for code
def morse_to_letters(morse_array):
    char_m = "?"
    for key, val in alphabet.items():
        if val == morse_array: return key
    return char_m

def time_to_morse(time_array, cutoff):
    morse = ""
    for time in time_array:
        if time >= cutoff:
            morse = morse + "-"
        else:
            morse = morse + "."
    return morse
def auto_center(string):
    number = len(string)
    space = 10 - (number // 2)
    return (" " * space) + string

def write_to_sD(message):
    fp = open("/sd/data.txt", "a")
    if gps.has_fix:
        if gps.timestamp_utc.tm_year == 0:
                fp.write("\n Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}".format(
                gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
                gps.timestamp_utc.tm_mday,  # struct_time object that holds
                gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                gps.timestamp_utc.tm_min,  # month!
                gps.timestamp_utc.tm_sec,
                ) + " MESS_START#"+ message + "#")
        else:
            fp.write("\n Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}".format(
            gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
            gps.timestamp_utc.tm_mday,  # struct_time object that holds
            gps.timestamp_utc.tm_year,  # the fix time.  Note you might
            gps.timestamp_utc.tm_hour,  # not get all data like year, day,
            gps.timestamp_utc.tm_min,  # month!
            gps.timestamp_utc.tm_sec,
            ) + "  MESS_START#"+ message + "#")
    else:
        fp.write("\n {GPS DOWN} MESS_START#"+message+"#")
    fp.flush()
    fp.close()




# Intializing varibles
username = "ME :)"
cutoff = 5
screen_state = -1
prev_screen_state = 0
text_state = 1
cur_line = 1
prev_line = -1
max_lines = 1
btn_1_time = 0
btn_1_mes = []
btn_1_closed = 0
total_mes = ""
morse_prev = ""

#fp = open("/sd/data.txt", "r+")


#Boot up sequnce
i = 0
z = 0
while True:
    btn_4.update()
    gps.update()
    time.sleep(0.5)
    i += 1
    if i > 5:
        i = 0
        z+= 1
    if z > 20:
        z = 0
    if gps.has_fix:
       break
    if btn_4.fell:
        break
    lcd_1 = "GPS waiting for fix"
    lcd_2 = auto_center("Please wait")
    lcd_3 = auto_center( "." * i)
    lcd_4 = auto_center("-" * z)
    lcd.clear()
    lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)


#LCD layout
# Top = state cur in and updates
# 2nd, 3rd = Display information
# 4th idk
lcd_1 = auto_center("Welcome")
lcd_2 = " "
lcd_3 = " "
lcd_4 = auto_center("Done booting")
lcd.clear()
lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)

track_long = 0
track_lat = 0

screen_refresh = 0
refresh_true = False

#the code
while True:
    #Get Lora data
    refresh_true = False
    btn_1.update()
    btn_2.update()
    btn_3.update()
    btn_4.update()
    #also Used for time
    packet = rfm9x.receive(timeout=.05)
    #Get GPS DATA (Need to change it out of the loop)
    #gps.update()
    #Update screen every 20 cycles (1 second)
    screen_refresh += 1
    if screen_refresh > 20:
        screen_refresh = 0

    if btn_4.fell:
        btn_1_mes = []
        total_mes = ""
        prev_line = 0
        cur_line = 0
        screen_state += 1
        if screen_state == 5:
            screen_state = 0

    # If no packet was received during the timeout then None is returned.
    if screen_state == 4:
        lcd_1 = ""
        lcd_2 = auto_center("ACTIVE SEARCH")
        lcd_3 = auto_center(":O")
        lcd_4 = ""
        lcd.clear()
        lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
        while True:
            packet = rfm9x.receive()
            if packet is not None:
                #if active start recording to SD
                print(packet)
                #if all(0x20 <= byte <= 0x7E for byte in packet):
                lcd_1 = ""
                lcd_2 = auto_center("MESSAGE RECEIVED!")
                lcd_3 = auto_center("YIPPIE!")
                lcd_4 = auto_center(":)")
                lcd.clear()
                lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
                packet_text = str(packet, "ascii")
                rssi = rfm9x.last_rssi
                write_to_sD(str(packet_text))

                #uncomment to transmit
                total_mes = "Message Recevied! Thanks!"
                rfm9x.send(bytes(total_mes, "utf-8"))
                time.sleep(3)
                screen_state = 0
                break
                time.sleep(3)
            btn_4.update()
            if btn_4.fell:
                screen_state = 0
                break


    #TODO: Allow user to change settings in device prob not

    #track gps cords
    if screen_state == 3:
        gps.update()
        refresh_true = True
        if btn_2.value == False:
            lcd_1 = auto_center("Tracking State")
            lcd_2 = auto_center("Lat: " + str(gps.latitude))
            lcd_3 = auto_center("Long: " + str(gps.longitude))
            lcd_4 = auto_center("Current Positon")
        elif btn_3.fell:
            lcd_1 = ""
            lcd_2 = auto_center("CORDS CLEARED")
            lcd_3 = ""
            lcd_4 = ""
            track_lat = 0
            track_long = 0
            lcd.clear()
            lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
            time.sleep(2)

        elif gps.has_fix:
            if track_long == 0:
                lcd_1 = auto_center("Tracking State")
                lcd_2 = auto_center("No Cords!")
                lcd_3 = auto_center(":V")
                lcd_4 = ""

            else:
                long_diff = track_long - gps.longitude
                lat_diff = track_lat - gps.latitude

                lcd_1 = auto_center("Tracking State")
                lcd_2 = auto_center("Lat: " + str(lat_diff))
                lcd_3 = auto_center("Long: " + str(long_diff))
                lcd_4 = ""
        else:
            lcd_1 = auto_center("Tracking State")
            lcd_2 = auto_center("GPS not avaliable")
            lcd_3 = auto_center(":(")
            lcd_4 = ""


    #If in transmiting state
    if screen_state == 2:
        #translate data to morse and letters

        #time based morse (BTN1 logic)
        if btn_1.value:
            btn_1_time = btn_1_time + 1
            if btn_1_closed != 0:
                btn_1_mes.append(btn_1_closed)
            btn_1_closed = 0
        if btn_1.value == False:
            btn_1_time = 0
            btn_1_closed = btn_1_closed + 1

        #TODO: if in text_state 0, make it time based (one button plus send button)


        #if in text_state 1, make char spacing with second button
        if text_state == 1:
            #messag logic
            morse_mes = time_to_morse(btn_1_mes, cutoff)
            reg_char = morse_to_letters(morse_mes)
            if (btn_2.fell) & (len(btn_1_mes) == 0):
                total_mes = total_mes + " "
            if (btn_2.fell) & (len(btn_1_mes) != 0):
                total_mes = total_mes + reg_char
                btn_1_mes = []
            #Update lcd screen
            lcd_1 = auto_center("Writing State")
            lcd_2 = auto_center(morse_mes + " " + reg_char)
            lcd_3 = total_mes
            lcd_4 = " "
            if morse_mes != morse_prev:
                lcd.clear()
                lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
            morse_prev = morse_mes
        #TODO :if in text_state 2, make it operate like a paddle (binarry) ?? Probably not

        #TODO add custom commands to send gps data

            #Ask to send data
            if btn_3.fell and len(total_mes) != 0:
                #uncomment to start transmiting
                #todo : add date or time or both to the output message **** done at receving end
                #adding commands
                gps.update()
                if "?GPS" in total_mes:
                    if gps.has_fix:
                        total_mes = total_mes.replace('?GPS', "("+ str(gps.latitude)+"," + str(gps.longitude) + ")")
                    else:
                        total_mes = total_mes.replace('?GPS', "{GPS DOWN}")
                if "?TME" in total_mes:
                    if gps.has_fix:
                        hour = gps.timestamp_utc.tm_hour - 8
                        if hour < 0:
                            hour = 24 + hour
                        total_mes = total_mes.replace('?TME', "Time : {:02}:{:02}:{:02}".format(
                        hour,
                        gps.timestamp_utc.tm_min,
                        gps.timestamp_utc.tm_sec,
                        ))
                    else:
                        total_mes = total_mes.replace('?TIME', "{GPS DOWN}")
                if "?CP" in total_mes:
                    total_mes = total_mes.replace('?CP', "(" + str(track_lat) + "," + str(track_long) + ")")

                rfm9x.send(bytes(total_mes, "utf-8"))
                lcd_1 = auto_center("Writing State")
                lcd_2 = auto_center("Sending Message :)")
                lcd_3 = ""
                lcd_4 = ""
                lcd.clear()
                lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
                write_to_sD("SENT: " + total_mes)
                i = 0
                #standby mode till comfirmation message
                while True:
                    btn_4.update()
                    packet = rfm9x.receive(timeout=.5)
                    lcd_3 = auto_center( "." * i)
                    i += 1
                    if i > 5:
                        i = 0
                    lcd.clear()
                    lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
                    #Execetion time out
                    if btn_4.fell:
                        lcd_1 = auto_center("Writing State")
                        lcd_2 = auto_center("Message confirmation")
                        lcd_3 = auto_center("Failed :(")
                        lcd_4 = ""
                        lcd.clear()
                        lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
                        time.sleep(2)
                        write_to_sD("DNR: Better Luck Next Time")
                        break
                    #Message succesfully transmited
                    if packet is not None:
                        packet_text = str(packet, "ascii")
                        lcd_1 = auto_center("Writing State")
                        lcd_2 = auto_center("Message Recevied!")
                        lcd_3 = packet_text
                        lcd_4 = ""
                        lcd.clear()
                        lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
                        write_to_sD("RESPONSE: " + packet_text)
                        time.sleep(2)
                        break
                    rfm9x.send(bytes(total_mes + "\n", "utf-8"))


    #If in read mode, Display line by line of messages in sd Card
    if screen_state == 1:
        i = 0
        out = ""
        if (btn_3.fell):
            cur_line += 1
            if cur_line > max_lines:
                cur_line = 0
        if (btn_2.fell):
            cur_line -= 1
            if cur_line < 0:
                cur_line = max_lines
        with open("/sd/data.txt", "r") as f:
            line = f.readline()
            if cur_line == i:
                lcd_2 = line
            while line != '':
                line = f.readline()
                i += 1
                if i > max_lines:
                    max_lines = i
                if cur_line == i:
                    start = line.find('#') + 1
                    end = line.find('#', start)
                    if start >= 0 and end >= 0:
                        lcd_2 = line[start:end]
                        out = lcd_2
                    else:
                        lcd_2 = ""
        if len(lcd_2) == 0:
            lcd_2 = auto_center("End of Messages")

        lcd_1 = "Read_State"
        lcd_3 = ""
        lcd_4 = ""
        if cur_line != prev_line:
            lcd.clear()
            lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
        prev_line = cur_line
        if btn_1.fell:
            #isolate cords
            start = out.find('(') + 1
            end = out.find(')', start)
            if start >= 0 and end >= 0:
                out = out[start:end]
            else:
                out = ""
            numbers = out.split(",")
            if numbers[0] == '':
                break
            numbers = [float(num.strip()) for num in numbers]
            #cords
            print(numbers)
            track_long = numbers[1]
            track_lat = numbers[0]

            lcd_1 = auto_center("Copied Cords")
            lcd_2 = auto_center("Long: " + str(track_lat))
            lcd_3 = auto_center("Lat: " + str(track_long))
            lcd_4 = ""
            lcd.clear()
            lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
            time.sleep(2)
            prev_line = -1


    #If in home mode, Display time, date and home screen
    if screen_state == 0:
        refresh_true = True
        if gps.has_fix:
            gps.update()
            hour = gps.timestamp_utc.tm_hour - 8
            if hour < 0:
                hour = 24 + hour

            lcd_1 = auto_center("Good Night")
            if  5 < hour < 12:
                lcd_1 = auto_center("Good Morning")
            if  12 < hour < 17:
                lcd_1 = auto_center("Good Afternoon")
            if 17 < hour < 20:
                lcd_1 = auto_center("Good Evening")
            if gps.timestamp_utc.tm_year == 0:
                lcd_2 = " "
            else:
                lcd_2 = auto_center( "Date : {}/{}/{}".format(
                        gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
                        gps.timestamp_utc.tm_mday,  # struct_time object that holds
                        gps.timestamp_utc.tm_year,  # the fix time
                    ))
            lcd_3 = auto_center("Time : {:02}:{:02}:{:02}".format(
                    hour,  # not get all data like year, day,
                    gps.timestamp_utc.tm_min,  # month!
                    gps.timestamp_utc.tm_sec,
                ))
            lcd_4 = auto_center(":)")
        else:
            lcd_1 = auto_center("Welcome")
            lcd_2 = " "
            lcd_3 = " "
            lcd_4 = auto_center(":)")

    #update LCD screen
    if screen_state != prev_screen_state:
        lcd.clear()
        lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)

    if refresh_true == True:
        if screen_refresh == 19:
            lcd.clear()
            lcd.print(lcd_1 + "\n" + lcd_2 + "\n" + lcd_3 + "\n" + lcd_4)
    prev_screen_state = screen_state










