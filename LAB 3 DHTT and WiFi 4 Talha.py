# DHT22 connected to RPi PICO to read temperature and humidity and send
# them out via a web page which allows the browser user to turn the on board LED ON & OFF
# (c) Mike Sharp January 2024.
# 
# *********************************************************************************
# * THE LIBRARIES and DECLARATIONS
# *********************************************************************************
#Bring in all the libraries.
from machine import Pin, Timer, SPI
import time
from time import sleep  		# Make sure we have sleep for start up -
                                            		# we MUST NOT use it anywhere else
import dht
import network			#Handles connecting to Wifi
import urequests 		# Handles aspects of servicing network requests
from usocket import socket	# Ethernet support
# Instantiate the sensor object from the dht class constructed on
# GPIO pin 2 (Thats actually Pin 4 on the PICO but on the version with the Ethernet HAT we need
# to use another pin)
sensor = dht.DHT22(Pin(2))

# The create a timer object, DHTtimer, from the Timer class we will do the setting up later'
DHTtimer = Timer()

# Now a couple of global variables to hold our temperature and humidity readings.
# We don't actually need them yet but in our next lab we will need them.
temperature = 0.0
humidity = 0.0

# Set up the on board LED as we did in Lab 1.
# Use this line if using WizNet Ethernet HAT:
# led = Pin(25, Pin.OUT)
# If using Wifi use this line
led = Pin('LED', Pin.OUT)  
# **********************************************************************************
#
#                                WARNING
#
# Putting your credentials into the code like this is NOT SECURE so when you get to production you would
# need to use a loader app requests the credentials via a terminal of some sort - could be WEB based, 
# and stores them securely in the persistent memory of the device. 
# ****** DON’T EVEN THINK ABOUT USING YOUR UNI or COMMERCIAL SSID or PASSWORDS. *******
# FOR NOW you can use your phone hotspot id / pword but before you leave the lab please ensure you delete 
# the SSID and # PASSWORD 
# **********************************************************************************
# Fill in your WiFi network name (ssid) and password here - probably best to use your phones hotspot
# to make this work - you will then need to connect you laptop to the same hotspot to see the web page. 
wifi_ssid = "TP-Link_5AF3"
wifi_password = "29905053"

wifi_ssid = "Talha"
wifi_password = "Samsung007"

# *********************************************************************************
# * THE SUBROUTINES / FUNCTIONS / METHODS 
# *********************************************************************************
# We put all the subroutines and functions we need to reuse anywhere in here.

# For now we only need a call back to update our readings every 3 or so seconds - the DHT22 is
# not reliable if you read it much faster than that, so it is not the sensor of choice for
# fast reactions!
def readDHT22(DHTtimer):
    global temperature, humidity		# Make the function update the global versions of these
                                        # variables and we can then access the values anywhere else
    sensor.measure()					# Read the sensors
    temperature = sensor.temperature()	# Copy the readings to the, now, global variables
    humidity = sensor.humidity()
    # Print it out.
    print("Temperature: {}°C   Humidity: {:.0f}% ".format(temperature, humidity))

def wifiConnect(ssid,password):
    # This function will attempt to connect to the wifi based on the credentials you entered
    # above, **************** it is not secure either ***************
    # but it is simple - we know we cannot actually do it this way for real but as part of
    # learning to use the tools we will be fine.
    #Connect to WLAN
    # Get the local Wifi System working
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Now try and connect to the Wifi we specified above
    wlan.connect(ssid, password)
    # Now wait for a connection - this whole LAB is no good without one so wait forever
    # until you have a connection.
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    
    # If we get past that 'While' then we have a connection so tell the world what hotspot / wifi / etc
    # we are connected to and most importantly tell us what our IP address is because we need to point our
    # browser at this IP address to see teh HTML page.
    print("WiFi Connection establied on: ",wifi_ssid, "\nEnsure your laptop is connected to ",wifi_ssid,
              " and point your browser at IP address:", wlan.ifconfig()[0], "\n")
    return wlan

def web_page():
    # This function does the work of creating the HTML that will be sent when the server is queried by a client
    # It starts by reading the state of the LED using the led.value method
    if led.value()==1:
        # If it is on it forces the led_state string to be "ON"
        led_state="ON"
    else:
        # Otherwise (its a digital world so if it is not ON then it is OFF so) set led_state = "OFF"
        led_state="OFF"
    #Now make sure we have access to the global temperatureand humidity
    global temperature, humidity
    
    # Set the string variables vTemp and cHum to the values of temperature and humidity - they will
    # no longer be numbers but strings (textual elements)
    cTemp = str(temperature)
    cHum = str(humidity)
    
    # Now we will create a chunck of HTML text which will be sent to the browser where it will be interpreted
    # and displayed. If you look down you will see the text is green (default Thonny setting) and there are a couple
    # of bits of black text which are the variables we want to insert into the HTML, the temperature and humidity
    # and the state of the onbaord LED. You can change the HTML if you want to experiment with a custom look and feel.
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talha's Raspberry Pi Pico Super sensor.</title>
    </head>
    <body>
    <div align="center">
    <H1>Talha's Raspberry Pi Pico Super sensor.</H1>
    <h2>Control LED</h2>
    PICO LED state: <strong>""" + led_state + """</strong>
    <p><a href="/?led=on"><button class="button">ON</button></a><br>
    </p>
    <p><a href="/?led=off"><button class="button button2">OFF</button></a><br>
    </p>
    <p> Current Temperature = """ + str(temperature) + """ &#8451; </P>
    <p> Current Humidity = """ + str(humidity) + """% </P>
    </div>
    </body>
    </html>
    """
    return html


# This is our main loop we will use a special structure to call this, and the it runs repeatedly.
def main(wlan):
    
    # DEBUG if needed print("Got here in main and forming up on IP " + ip_address)
    # Now we need to bind our IP to port 80 (HTML) so we can create a web page.
    s = socket()
    s.bind((wlan.ifconfig()[0],80))
    s.listen(5)
    
    # Now loop round for ever here just waiting for any browser to request our web page
    # and if it comes with one of the two 'request' extensions to the URL eg '/?led=on'
    # take the appropriate action. Deal with the LED either turn it ON or OFF
    # and respond with a new web page which the browser will display to the user.
    # It uses some quite sophisticated techniques to do its work - you can look them up to
    # learn more about things like conn.send(',,,,,,,,,,') etc.
    while True:
        conn, addr = s.accept()
        print('Request from %s' % str(addr))
        request = conn.recv(1024)
        request = str(request)
        #print('Content = %s' % request)
        led_on = request.find('/?led=on')
        led_off = request.find('/?led=off')
        if led_on == 6:
            print("LED ON")
            led.value(1)
        if led_off == 6:
            print("LED OFF")
            led.value(0)
        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Connection: close\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Content-Length: %s\n\n' % len(response))
        conn.send(response)
        conn.close()


# *********************************************************************************
# * THE SETUP processes 
# *********************************************************************************

# First lets get connected to the (your) local Wifi hotspot / home / Uni (IoT)
wlan = wifiConnect(wifi_ssid, wifi_password)

# *********************************************************************************
# * THE CALLBACKS 
# *********************************************************************************
# We set them up here after the SUBROUTINES / FUNCTIONS that will be called back
# otherwise we could get an error depending on the way our IDE handles any compiling
# or dependancy that might be needed.

# So here is out call back to handle the temperature / humidity reading taking.
DHTtimer.init(period=3000, mode=Timer.PERIODIC, callback=readDHT22)

# *********************************************************************************
# * THE MAIN LOOP 
# *********************************************************************************
# Actually we are just going to let the system find and run the main function, defined above, over and over again.
#
if __name__ == "__main__":
    main(wlan) 

