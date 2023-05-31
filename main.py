import utime
import network
import metoffice_wow
import rp2
import time
import read_hmt
import setup
import settings
import gc
import temps_file
import NTP_sync
import machine

# Setup UART port for user interaction to e.g. change settings
# noinspection PyArgumentList
uart1 = machine.UART(1, 9600, parity=None, stop=1, bits=8, rx=machine.Pin(5),
                     tx=machine.Pin(4), timeout=30000)

led = machine.Pin("LED", machine.Pin.OUT)
led.on()

# User interaction over UART port
print('Waiting 30 secs for any user interaction on UART1...')
# user_setup.do_setup(uart1)
setup.do_setup(uart1)

# Use a 'settings.py' file to provide WiFi passwords etc.
ssid = str(settings.SETTINGS['SSID'])
password = str(settings.SETTINGS['WIFI-PASSWORD'])
rp2.country('GB')

# Get settings for WoW transmissions
wow_site_id = str(settings.SETTINGS['WOW_SITE_ID'])
wow_auth_key = str(settings.SETTINGS['WOW_AUTH_KEY'])

# Number of temperature readings required before submitting
# a daily max/min report
data_points_req = 100

# Interval between sensor readings in milliseconds
sensor_read_intv = 60000

# 1=daily Max only, 2=daily Max/Min only, 3= daily Max/Min and hourly
reporting_sched = int(settings.SETTINGS['REPORTING_SCHED'])
utime.sleep(1)
led.off()

# Setup WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)
wlan.connect(ssid, password)

uart1.write('\r\nProceeding to WiFi setup...')
print('Proceeding to WiFi setup...')
# Wait for connect or fail
max_wait = 15
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('Waiting for connection...')
    uart1.write('\r\nWaiting for connection...')
    time.sleep(1)

if wlan.status() != 3:
    uart1.write('\r\nNetwork connection failed...')
    machine.reset()

else:
    print('WiFi connected...')
    uart1.write('\r\nWiFi connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
    uart1.write('\r\nip = ' + status[0])
    print('Attempting NTP time sync...')
    uart1.write('\r\nAttempting NTP time sync...')
    NTP_sync.set_ntp_time()
    print('Completed NTP time sync...')
    uart1.write('\r\nCompleted NTP time sync...')
    print(time.localtime())
    uart1.write('\r\n' + str(time.localtime()))

# Set some timing start points
last_reading_msec = utime.ticks_ms()
last_minute = utime.localtime()[4]
last_hour = utime.localtime()[3] - 1
last_day = utime.localtime()[2] - 1

print('Getting HMT reading...')
uart1.write('\r\nGetting HMT reading...')
led.on()
# Make a few data requests to ensure HMT has responded with a temperature
read_hmt.get_hmt_temp()
read_hmt.get_hmt_temp()
temp = read_hmt.get_hmt_temp()
print('Temp C= ' + str(temp))
uart1.write('\r\nCalibrated Temp C = ' + str(temp))
led.off()

print('Loading previous temp data if available and recent....')
uart1.write('\r\nLoading previous temp data if available and recent....')
max_temp, min_temp, count = temps_file.load_temps()

# Set our initial temp max/min and temperature readings count based
# on if recent readings are available (from above) or not
if temp and max_temp and min_temp and count is not None:
    print('Temp OK, prev max/min avail')
    prev_temp = temp
    print(count, temp, max_temp, min_temp)

elif temp is not None:
    print('Temp OK - prev max/min NOT avail')
    max_temp = temp
    min_temp = temp
    count = 1
    prev_temp = temp
    print(count, temp, max_temp, min_temp)

print('Entering main loop - reading sensor every ' + str(
    int(sensor_read_intv/1000)) + ' secs')
uart1.write('\r\nCommencing operation')
uart1.write('\r\nReading sensor every ' + str(int(sensor_read_intv/1000))
            + ' secs')

# main loop, steady LED flash if connected to WiFi
while True:
    if wlan.isconnected():
        led.on()
        utime.sleep_ms(100)
        led.off()
    # Read the HMT every 'sensor_read_intv' milliseconds
    current_time = utime.ticks_ms()
    if utime.ticks_diff(current_time, last_reading_msec) > sensor_read_intv:
        led.on()
        temp = read_hmt.get_hmt_temp()
        uart1.write('\r\nTemp = ' + str(temp))
        utime.sleep(1)
        # Update our temperature values
        if temp is not None:
            led.off()
            count += 1
            if temp > max_temp:
                max_temp = temp
            elif temp < min_temp:
                min_temp = temp
            prev_temp = temp
            last_reading_msec = current_time
            print(utime.localtime())
            print('Readings:' + str(count) + ' Temp:' + str(temp) +
                  ' Max:' + str(max_temp) + ' Min:' + str(min_temp))
            print('MEM free: ' + str(gc.mem_free()))

            print('Saving temperatures to file....')
            temps_file.save_temps(max_temp, min_temp, count)

    # Hourly tasks
    current_minute = utime.localtime()[4]
    current_hour = utime.localtime()[3]
    if current_hour != last_hour and current_minute == 50 \
            and reporting_sched == 3:
        uart1.write('\r\nSending WoW report...')
        send_wow = metoffice_wow.send_wow(wlan, ssid, password, wow_site_id,
                                          wow_auth_key, temp)
        uart1.write('\r\nWoW result (201 = success): ' + send_wow)
        last_hour = current_hour

    # Daily tasks
    current_day = utime.localtime()[2]
    if current_day != last_day and current_hour == 9 and \
            current_minute == 0 and count > data_points_req:
        uart1.write('\r\nSending WoW report...')
        if reporting_sched == 1:  # daily max temp only
            send_wow = metoffice_wow.send_wow(wlan, ssid, password,
                                              wow_site_id, wow_auth_key,
                                              temp, max_temp)
            uart1.write('\r\nWoW result (201 = success): ' + send_wow)
        else:
            send_wow = metoffice_wow.send_wow(wlan, ssid, password,
                                              wow_site_id, wow_auth_key,
                                              temp, max_temp, min_temp)
            uart1.write('\r\nWoW result (201 = success): ' + send_wow)
        max_temp = temp
        min_temp = temp
        count = 0
        last_day = current_day

        # daily NTP time sync
        NTP_sync.set_ntp_time()

    # wait for 1 second
    utime.sleep(1)
