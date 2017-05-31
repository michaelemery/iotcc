#!/usr/bin/env python

from socket import *
import json
from datetime import datetime
import requests


def http_request2(event_entry):
    # this is rewritten with the requets library to work with the microhort.com server.
    # the old function is kept just incase.
    message = json.dumps(event_entry)

    serverName = "http://www.microhort.com:5000"
    url = serverName + "/submitdatalog"

    try: 
        values = {'log' : str(message)}
        r=requests.post(url,data=values)
        print (" ******  EVENT LOGGED TO SERVER ****** : " + r.text)
        response = r.status_code
    except:
        response = "408 request timed out"
        print("failed!")

    if '200' not in str(response):

        event_backlog = open('eventLog_backlog.txt', 'a')
        event_backlog.write(message+"\n")
        event_backlog.close()
        print("unable to write event to database, so has been logged locally")
        return "the event was unable to be logged to the database, so has been logged locally"
    else:
        event_backlog = open('eventLog_backlog.txt','r')
        past_events = event_backlog.readlines()
        event_backlog.close()
        if not past_events == "":
            for event in past_events:
                # Connect to the server at the specified port
                values = {'log' : str(event)}
                r=requests.post(url,data=values)
                response = r.status_code
                print(" **** EVENT BACKLOG UPLOADED ****")
                if '200' in str(response):
                    past_events.remove(event)
                else:
                    pass
            event_backlog = open('eventLog_backlog.txt','w')
            event_backlog.writelines(past_events)
        else:
            return "The event has been logged successfully"

def http_request(event_entry):

    message = json.dumps(event_entry)

    print ("message is: "+message)
    # Address for the server
    serverName = 'localhost' # http://www.microhort.com refuses to work here. hmm?

    # Server's listening port
    serverPort = 8080

    # Create the socket object
    clientSocket = socket(AF_INET, SOCK_STREAM)
    try:
        # Connect to the server at the specified port
        clientSocket.connect((serverName,serverPort))

        request = "HEAD / HTTP/1.0\nHost:localhost\n\n"+str(message)

        ## Send the message
        clientSocket.send(request.encode())

        ## Receive the reply
        response = clientSocket.recv(1024)
        #return response
        # For print the response
        print('From Server:', response)
        clientSocket.close()
    except: #ConnectionRefusedError:
        response = "408 request timed out"
    if '200' not in str(response):

        event_backlog = open('eventLog_backlog.txt', 'a')
        event_backlog.write(message+"\n")
        event_backlog.close()
        print("unable to write event to database, so has been logged locally")
        return "the event was unable to be logged to the database, so has been logged locally"
    else:
        event_backlog = open('eventLog_backlog.txt','r')
        past_events = event_backlog.readlines()
        event_backlog.close()
        if not past_events == "":
            for event in past_events:
                # Connect to the server at the specified port
                clientSocket = socket(AF_INET, SOCK_STREAM)
                clientSocket.connect((serverName,serverPort))
                print('message is',event)
                request = "HEAD / HTTP/1.0\nHost:localhost\n\n"+str(event)

                ## Send the message
                clientSocket.send(request.encode())
                response = clientSocket.recv(1024)
    #return response
    # For print the response
                print('From Server:', response)
                clientSocket.close()
                if '200' in str(response):
                    past_events.remove(event)
                else:
                    break
            event_backlog = open('eventLog_backlog.txt','w')
            event_backlog.writelines(past_events)
        else:
            return "The event has been logged successfully"


print ("starting request")
event_entry = {
        'event_dtg': str(datetime.now()),
        'event_hub_id': 3,
        'event_profile_id': 3,
        'event_sensor_type_id': 3,
        'event_state': 3,
        'event_message': 'too hot'
    }
http_request2(event_entry)
