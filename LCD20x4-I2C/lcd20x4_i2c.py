#!/usr/bin/env python2.7
"""Handle messages from Node-RED and display them on the LCD"""

# Topic: Send message to 20x4 LCD
#
# file : LCD20x4-I2C.py

import time
import threading
import json
import sys
import math
import lcddriver

if len(sys.argv) == 5:
    CMD = sys.argv[1].lower()
    LCD_TYPE = sys.argv[2].lower()
    SCROLL_SPEED = int(sys.argv[3])
    lcddriver.ADDRESS = int(sys.argv[4], 16)

lcd_error = False;

try:
    LCD = lcddriver.lcd()
except:
    print("LCD Not Found - Check Addess and Connections")
    lcd_error = True;

if (not lcd_error):
    STARTUPMSG = ["       SYSTEM       ",
                  "       START        ",
                  "         UP         ",
                  "                    "]

    SHUTDOWNMSG = ["       SYSTEM       ",
                   "        SHUT        ",
                   "        DOWN        ",
                   " "]

    ERRORMSG = ["       ERROR        ",
                "      DETECTED      ",
                " ",
                " "]

    CLS = [" ",
           " ",
           " ",
           " "]

    def translate(value, left_min, left_max, right_min, right_max):
        """Translate string (handles scrolling effect)"""
        global UPDATE_SCREEN_THREAD_STOP
        if (left_min > left_max or right_min > right_max or value < left_min or value > left_max or
                not isinstance(value, (int, int, float, complex))):
            if not isinstance(value, (int, int, float, complex)):
                error = "Scroll Speed Value NaN"
            else:
                error = "Scroll Speed Value Error"
            updatescreen(ERRORMSG, SCROLL_SPEED, UPDATE_SCREEN_THREAD_STOP)
            print(error)
            return False
        else:
            left_span = left_max - left_min
            right_span = right_max - right_min
            value_scaled = float(value - left_min) / float(left_span)
            return right_min + (value_scaled * right_span)

    def updatescreen(input_msg, sleep, stop_event):
        """Send message to screen"""
        sleep = translate(sleep, 1, 10, 0.1, 2) #update this range to affect scroll speed
        if not sleep:
            return
        messages = [input_msg[0], input_msg[1], input_msg[2], input_msg[3]]
        scrollinglines = []

        for number in range(0, 4):
            if len(messages[number]) > 20:
                truncated = messages[number][:19] + "*"
                scrollinglines.append(number)
            else:
                truncated = messages[number] + " "*(20 - len(messages[number]))

            LCD.lcd_display_string(truncated, number+1)
            time.sleep(0.05)

        while (not stop_event.is_set() and scrollinglines):
            for line in scrollinglines:
                LCD.lcd_display_string(messages[line][:19] + "*", line+1)
                time.sleep(sleep*1.5)
                for character in range(1, len(messages[line])-18):
                    if stop_event.is_set():
                        break
                    if character >= len(messages[line]) - 19:
                        truncated = "*" + messages[line][character:character+19]
                    else:
                        truncated = "*" + messages[line][character:character+18] + "*"
                    LCD.lcd_display_string(truncated, line+1)
                    time.sleep(sleep)
                if stop_event.is_set():
                    for reset_line in range(0, 4):
                        LCD.lcd_display_string(" "*20, reset_line+1)
                    break
                else:
                    time.sleep(sleep*1.5)

    UPDATE_SCREEN_THREAD_STOP = threading.Event()
    UPDATE_SCREEN_THREAD = threading.Thread(target=updatescreen, args=(STARTUPMSG, SCROLL_SPEED, UPDATE_SCREEN_THREAD_STOP))
    UPDATE_SCREEN_THREAD.start()

    def pad_str(pos, input_str):
        """Pad leading spaces if pos has a value"""
        global UPDATE_SCREEN_THREAD_STOP
        if (isinstance(input_str, str) and isinstance(pos, (int, int, float, complex)) and
                pos > 0 and pos <= 20):
            input_str = " "*(pos-1) + input_str
            return input_str
        else:
            if not isinstance(input_str, str):
                error = "Message not a String"
            if not isinstance(pos, (int, int, float, complex)):
                error = "Message Position NaN"
            elif (pos < 1 or pos >= 20):
                error = "Message Position not 1-20"
            updatescreen(ERRORMSG, SCROLL_SPEED, UPDATE_SCREEN_THREAD_STOP)
            print(error)
            return False

    def center_str(input_str):
        """Center the string based on length"""
        if isinstance(input_str, str):
            pad = int(math.floor(((20-len(input_str))/2)))
            input_str = " "*(pad) + input_str
            return input_str
        else:
            print("Message not a String")
            return False

    def main():
        """main function"""
        global UPDATE_SCREEN_THREAD
        global UPDATE_SCREEN_THREAD_STOP

        if CMD == "writelcd":
            if LCD_TYPE == "20x4":
                while True:
                    try:
                        data = input()
                        if data == 'close':
                            if UPDATE_SCREEN_THREAD.is_alive():
                                UPDATE_SCREEN_THREAD_STOP.set()
                                while UPDATE_SCREEN_THREAD.is_alive():
                                    time.sleep(0.05)
                            updatescreen(SHUTDOWNMSG, SCROLL_SPEED, UPDATE_SCREEN_THREAD_STOP)
                            sys.exit(0)
                        else:
                            if UPDATE_SCREEN_THREAD.is_alive():
                                UPDATE_SCREEN_THREAD_STOP.set()
                                while UPDATE_SCREEN_THREAD.is_alive():
                                    time.sleep(0.05)
                            json_error = False
                            #speederror = False
                            poserror = False
                            centererror = False
                            try:
                                data = json.loads(data)
                            except:
                                print("Input not a JSON Message")
                                json_error = True
                            if not json_error:
                                msg = []
                                for line in range(0, 4):
                                    try:
                                        if data['msgs'][line]['center'] is True:
                                            if len(data['msgs'][line]['msg']) < 21:
                                                msg.append(center_str(data['msgs'][line]['msg']))
                                                if not msg[line]:
                                                    centererror = True
                                                    break
                                            else:
                                                msg.append(data['msgs'][line]['msg'])
                                        else:
                                            raise KeyError
                                    except KeyError:
                                        try:
                                            msg.append(pad_str(data['msgs'][line]['pos'],
                                                               data['msgs'][line]['msg']))
                                            if not msg[line]:
                                                poserror = True
                                        except KeyError:
                                            print("POS or msg Value Missing")
                                            poserror = True
                                            break
                                if not poserror and not centererror:
                                    UPDATE_SCREEN_THREAD_STOP = threading.Event()
                                    UPDATE_SCREEN_THREAD = threading.Thread(target=updatescreen, args=(msg, SCROLL_SPEED, UPDATE_SCREEN_THREAD_STOP))
                                    UPDATE_SCREEN_THREAD.start()
                                else:
                                    updatescreen(ERRORMSG, 3, UPDATE_SCREEN_THREAD_STOP)
                            else:
                                updatescreen(ERRORMSG, 3, UPDATE_SCREEN_THREAD_STOP)
                    except (EOFError, KeyboardInterrupt):
                        if UPDATE_SCREEN_THREAD.is_alive():
                            UPDATE_SCREEN_THREAD_STOP.set()
                            while UPDATE_SCREEN_THREAD.is_alive():
                                time.sleep(0.05)
                        updatescreen(SHUTDOWNMSG, 3, UPDATE_SCREEN_THREAD_STOP)
                        sys.exit(0)
                    except SystemExit:
                        if UPDATE_SCREEN_THREAD.is_alive():
                            UPDATE_SCREEN_THREAD_STOP.set()
                            while UPDATE_SCREEN_THREAD.is_alive():
                                time.sleep(0.05)
                        updatescreen(SHUTDOWNMSG, 3, UPDATE_SCREEN_THREAD_STOP)
                        sys.exit(0)
        else:
            print("Bad parameters - accepts writelcd {screensize}")

    if __name__ == '__main__':
        main()
