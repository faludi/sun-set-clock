# Uses a BBC micro:Bit with Grove shield and light sensor to 
# create a clock that sets itself using the sun.
# Rob Faludi, faludi.com, June 2018

from microbit import display, sleep, running_time, button_a, button_b, Image, pin0
from math import trunc

day_length = 86400000
daylight_threshold = 60
hysteresis = 10
midnight = running_time()
sunrise = None
sunset = None
noon = None
daytime_length = None
light_array = []
light_average = 0
daytime_length_array = []
ctr = 0
d_ctr = 0
# FIX TO BE 15 RATHER THAN 1
update_interval = 15 * 60 * 1000 / 100  # in milliseconds
last_update = 0
display_clear_time = 0
last_daytime_length = 0

print("Sun Set Clock 1.02 Start...")


def get_time():
    day_time = ((running_time() - midnight) % day_length) / 1000
    hours = trunc(day_time / 3600)
    minutes = trunc((day_time % 3600) / 60)
    seconds = trunc(day_time % 60)
    return [hours, minutes, seconds]


def get_time_string(show_seconds=False):
    hours, minutes, seconds = get_time()
    if hours < 10:
        hours = "0" + str(hours)
    else:
        hours = str(hours)
    if minutes < 10:
        minutes = "0" + str(minutes)
    else:
        minutes = str(minutes)
    time_string = (hours + ":" + minutes)
    if show_seconds:
        if seconds < 10:
            seconds = "0" + str(seconds)
        else:
            seconds = str(seconds)
        time_string = (hours + ":" + minutes + ":" + seconds)
    return time_string


def read_light_sensor():
    light = pin0.read_analog()
    return light


def setting_mode(threshold):
    while (button_a.is_pressed() or button_b.is_pressed()):
        display.show(Image.CLOCK12)
        sleep(300)
        display.show(Image.CLOCK3)
        sleep(300)
        display.show(Image.CLOCK6)
        sleep(300)
        display.show(Image.CLOCK9)
        sleep(300)
        display.clear()
    display.show(threshold)
    sleep(300)
    display.show(Image.ARROW_E)
    sleep(400)
    display.show(Image.ARROW_W)
    sleep(400)
    display.clear()
    last_click = running_time()
    while (running_time() < last_click + 5000):
        if button_b.was_pressed():
            last_click = running_time()
            threshold = threshold + 1
            display.show(Image.ARROW_N)
            sleep(300)
            display.show(threshold)
            sleep(300)
            display.clear()
        if button_a.was_pressed():
            last_click = running_time()
            threshold = threshold - 1
            display.show(Image.ARROW_S)
            sleep(300)
            display.show(threshold)
            sleep(300)
            display.clear()
        
    tfile = open("tstore", "w")
    tfile.write(str(threshold))
    tfile.close()
    display.show(Image.YES)
    sleep(700)
    display.clear()
    return(threshold)
            

# MAIN PROGRAM
# update daylight threshold from flash storage
try:
    tfile = open("tstore", "r")
    daylight_threshold = int(tfile.read())
    tfile.close()
except OSError:
    print("No tfile")

last_light = read_light_sensor()

# guess day or night on startup
if read_light_sensor() > daylight_threshold:
    midnight = running_time() - (12 * 60 * 60 * 1000)
else:
    midnight = running_time()

while True:
    # set current thresholds
    sunrise_threshold = daylight_threshold + (hysteresis/2)
    sunset_threshold = daylight_threshold - (hysteresis/2)

    # display the time when the left button is pressed
    if button_a.was_pressed():
        display.show(get_time_string())
        display.clear()
        print("Time:", get_time_string(show_seconds=True))
    # debug output when the right button is pressed
    if button_b.was_pressed():
        print("light avg", light_average)
        display.show(str(round(light_average)))
        sleep(300)
        display.clear()
        # go into setting mode if the right button is held down
        if button_b.is_pressed():
            press_time = running_time()
            while (button_b.is_pressed()):
                display.show(Image.DIAMOND_SMALL)
                if (running_time() - press_time > 1500):
                    daylight_threshold = setting_mode(daylight_threshold)
                display.clear()

    # read light levels periodically and update clock as needed
    if (running_time() > (last_update + update_interval) or last_update == 0):
        try:
            light_array[ctr] = read_light_sensor()
        except IndexError:
            light_array.append(read_light_sensor())
        ctr += 1
        if ctr >= 100:
            ctr = 0

        light_average = sum(light_array) / len(light_array)

        # detect sunrise and sunset
        if light_average >= sunrise_threshold and last_light < sunrise_threshold:
            # guess morning on first sunrise
            if sunrise is None:
                midnight = running_time() - (6 * 60 * 60 * 1000)
            sunrise = running_time()
            print("Sunrise at: ", sunrise)
            display.show(Image.ARROW_N)
            display_clear_time = sunrise + 15 * 60 * 1000
        if light_average <= sunset_threshold and last_light > sunset_threshold:
            # guess evening on first sunset
            if sunset is None:
                midnight = running_time() - (18 * 60 * 60 * 1000)
            sunset = running_time()
            print("Sunset at: ", sunset)
            display.show(Image.ARROW_S)
            display_clear_time = sunset + 15 * 60 * 1000
        last_light = light_average

        # clear display when needed
        if display_clear_time > 0 and running_time() > display_clear_time:
                display.clear()
                display_clear_time = 0

        # set the clock
        if sunrise is not None and sunset is not None:
            if sunset-sunrise > 0:
                daytime_length = sunset - sunrise
            if daytime_length != last_daytime_length:
                try:
                    daytime_length_array[d_ctr] = daytime_length
                except IndexError:
                    daytime_length_array.append(daytime_length)
                d_ctr += 1
                if d_ctr >= 7:
                    d_ctr = 0
                for item in daytime_length_array:
                    print(item)
                daytime_length_average = sum(daytime_length_array) / len(daytime_length_array)
                last_daytime_length = daytime_length
                print("Day length avg:", daytime_length_average)
            noon = sunset - (daytime_length_average / 2)
            midnight = noon - (day_length / 2)

        # schedule for next update
        last_update = running_time()