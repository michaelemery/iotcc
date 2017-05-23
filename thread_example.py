#!/usr/bin/python
import random
import _thread

X = [0]
Y = [0]

try:
    thread.start_new_thread(checker, (X,Y))
except:
    print("failed to start thread")

main(X,Y)

def main(x,y):
    while True:
        r = random.random()
        if (r > 0.9):
            x[0] = 1
            y[0] = 1
        elif (r < 0.1):
            x[0] = -1
            y[0] = -1
        elif (r > 0.5 and r < 0.55):
            x[0] = 0
            y[0] = 0
        time.sleep(0.3)

def checker(x,y):
    while True:
        if x[0] == 1:
            print ("x = 1")
        elif x[0] == 2: 
            print ("x = 2")
        elif x[0] == 3:
            print ("x = 3")
        if y[0] == 1:
            print ("y = 1")
        elif y[0] == 2: 
            print ("y = 2")
        elif y[0] == 3:
            print ("y = 3")
        time.sleep(0.5)
