"""EE 250L Lab 10 Signal Processing

This file is the starter code for the lab assignment.

TODO: List team members here.

TODO: Insert Github repository link here.

"""

import paho.mqtt.client as mqtt
import time
import requests
import json
from datetime import datetime

# MQTT variables
broker_hostname = "eclipse.usc.edu"
broker_port = 11000

#uncomment these lines to subscribe to real-time published data
ultrasonic_ranger1_topic = "ultrasonic_ranger1/real_data"
ultrasonic_ranger2_topic = "ultrasonic_ranger2/real_data"

#uncomment these lines to subscribe to recorded data being played back in a loop
# ultrasonic_ranger1_topic = "ultrasonic_ranger1/fake_data"
# ultrasonic_ranger2_topic = "ultrasonic_ranger2/fake_data"

# Lists holding the ultrasonic ranger sensor distance readings. Change the 
# value of MAX_LIST_LENGTH depending on how many distance samples you would 
# like to keep at any point in time.
MAX_LIST_LENGTH = 8
ranger1_dist = []
#moving average
ranger1_average=[]
#differential
ranger1_delta=[]
ranger2_dist = []
#moving average
ranger2_average=[]
#differential
ranger2_delta=[]
def ranger1_callback(client, userdata, msg):
    if int(msg.payload)>220:
        return
    global ranger1_dist
    ranger1_dist.append(int(msg.payload))
    #truncate list to only have the last MAX_LIST_LENGTH values
    ranger1_dist = ranger1_dist[-MAX_LIST_LENGTH:]
    buffer=0
    for i in ranger1_dist:
        buffer+=int(i)
    global ranger1_average
    buffer/=len(ranger1_dist)
    ranger1_average.append(buffer)
    ranger1_average=ranger1_average[-MAX_LIST_LENGTH:]
    global ranger1_delta
    if len(ranger1_dist)>1:
        if ranger1_dist[-1]-ranger1_dist[-2]>120:
            ranger1_delta.append(120)
        else:
            ranger1_delta.append(ranger1_dist[-1]-ranger1_dist[-2])
    ranger1_delta=ranger1_delta[-MAX_LIST_LENGTH:]

def ranger2_callback(client, userdata, msg):
    if int(msg.payload)>300:
        return
    global ranger2_dist
    ranger2_dist.append(int(msg.payload))
    #truncate list to only have the last MAX_LIST_LENGTH values
    ranger2_dist = ranger2_dist[-MAX_LIST_LENGTH:]
    buffer = 0
    global ranger2_average
    for i in ranger2_dist:
        buffer += int(i)
    buffer /= len(ranger2_dist)
    ranger2_average.append(buffer)
    ranger2_average = ranger2_average[-MAX_LIST_LENGTH:]
    global ranger2_delta
    if len(ranger2_dist)>1:
        if ranger2_dist[-1]-ranger2_dist[-2]>120:
            ranger2_delta.append(120)
        else:
            ranger2_delta.append(ranger2_dist[-1]-ranger2_dist[-2])
    ranger2_delta=ranger2_delta[-MAX_LIST_LENGTH:]
# The callback for when the client receives a CONNACK response from the server.

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(ultrasonic_ranger1_topic)
    client.message_callback_add(ultrasonic_ranger1_topic, ranger1_callback)
    client.subscribe(ultrasonic_ranger2_topic)
    client.message_callback_add(ultrasonic_ranger2_topic, ranger2_callback)

# The callback for when a PUBLISH message is received from the server.
# This should not be called.
def on_message(client, userdata, msg): 
    print(msg.topic + " " + str(msg.payload))

if __name__ == '__main__':
    # Connect to broker and start loop    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_hostname, broker_port, 60)
    client.loop_start()

    hdr = {
        'Content-Type': 'application/json',
        'Authorization': None #not using HTTP secure
    }

    state = 0
    stateS = 0
    timeout = 0
    while True:
        """ You have two lists, ranger1_dist and ranger2_dist, which hold a window
        of the past MAX_LIST_LENGTH samples published by ultrasonic ranger 1
        and 2, respectively. The signals are published roughly at intervals of
        200ms, or 5 samples/second (5 Hz). The values published are the 
        distances in centimeters to the closest object. The measurements can
        technically take values up to 1024, but you will mainly see values 
        between 0-700. Jumps in values will most likely be from 
        inter-sensor-interference, so be sure to filter the signal accordingly
        to remove these jumps. 
        """
        
        # TODO: detect movement and/or position

        print("ranger1: " + str(ranger1_dist[-1:]) + ", ranger2: " + 
            str(ranger2_dist[-1:])) 
        '''
        if int(ranger1_average[-1])<int(ranger2_average[-1]):
            print("still--left")
        if int(ranger1_average[-1])>int(ranger2_average[-1]):
            print("still--right")
        '''
    #tracking state using state
        '''
        0 --original state
        1--moving  right 
        2--moving  left
        3 still and on the left side
        4 still and on the right side
        5 still and in the middle
        '''

        #triggered the left sensor, getting close
        if len(ranger1_delta)>2:
            if int(ranger1_delta[-3]) < -15 or int(ranger1_delta[-2])< -15 and int(ranger1_delta[-1])<6:
                if int(ranger1_average[-1]+ranger1_average[-2]-ranger1_average[-3]-ranger1_average[-4])<=-8:
                #if int(ranger1_average[-1]-ranger1_average[-3])<=-5 or int(ranger1_average[-1]-ranger1_average[-2])<=-4:
                    stateS=1
                    if state==0:
                        state=1
                        timeout=12
                    elif state==1:
                        timeout=12
                        state=1
                    elif state==2:
                        state=2
                        timeout=12
                    elif state==3:
                        state=1
                        timeout=12
                    elif state==5:
                        state=2
                        timeout=12
        #triggered the right sensor, getting close
        if len(ranger2_delta) > 2:
            if int(ranger2_delta[-3]) < -15 or int(ranger2_delta[-2]) < -15 and int(ranger2_delta[-1])<6:
                if int(ranger2_average[-1]+ranger2_average[-2]-ranger2_average[-3]-ranger2_average[-4])<=-8:
                        #or int(ranger2_average[-1]-ranger2_average[-2])<=-4:
                    stateS=2
                    if state==0:
                        state=2
                        timeout=12
                    elif state == 2:
                        timeout=12
                    elif state==5:
                        state=1
                        timeout = 12
                    elif state==4:
                        state=2
                        timeout=12
                    elif state==1:
                        state=1
                        timeout=12

        if len(ranger2_delta) > 1 and len(ranger1_delta)>1:
            if abs(ranger2_delta[-1])<4 and abs(ranger2_delta[-2]) < 4:
                if abs(ranger1_delta[-1])<4 and abs(ranger1_delta[-2]) < 4:
                    if state==0:
                        state=0
                    elif state==1:
                        if stateS==1 and timeout==0:
                            state=5
                        elif stateS==2 and timeout==0:
                            state=4
                    elif state==2:
                        if stateS == 1 and timeout == 0:
                            state=3
                        elif stateS == 2 and timeout == 0:
                            state=5
        message=""
        sendmessage=0
        if state==1:
            print("moving right")
            message="moving right"
            sendmessage=1
        if state==2:
            print("moving left")
            sendmessage=1
            message="moving left"
        if len(ranger1_dist)>1:
            if int(ranger1_dist[-1])<140 or int(ranger2_dist[-1])<120:
                sendmessage=1
                if state==3:
                    print("still-left")
                    message="still-left"
                if state==4:
                    print("still-right")
                    message="still-right"
                if state==5:
                    if ranger1_average[-1:]>ranger2_average[-1:]:
                        print("still-right")
                        message="still-right"
                    elif ranger1_average[-1:]<ranger2_average[-1:]:
                        print("still-left")
                        message="still-left"

        #print("timeout: "+str(timeout))
        #print("state: "+ str(state))
        #print("stateS: "+str(stateS))
        #print("average1: "+str(ranger1_average))
        #print("average2: "+str(ranger2_average))
        if timeout>0:
            timeout=int(timeout)-1
        #the http posting process
        if sendmessage==1:
            payload = {
            'time': str(datetime.now()),
            'event': message
            }
            response = requests.post("http://0.0.0.0:5000/post-event", headers = hdr,
                                data = json.dumps(payload))
            print(response.json())
            sendmessage=0
            message=""
        time.sleep(0.2)