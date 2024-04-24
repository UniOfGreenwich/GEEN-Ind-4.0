# Here is a simple start to making AR a thing Mike Sharp March / April 2024.
# All these code samples are VERY CRUDE, but they will give you a good idea
# of how easy it is to create 'AR' content in code.
# This one is the crudest of the lot.
# It uses the two big libraries and associated connections:
# Google 'mediapipe' library which has a vast array of pre-trained
# algorithms and we will just use the one for hands. You can learn a lot more
# about mediapipe here: https://learnopencv.com/introduction-to-mediapipe/
# The 'CV2' library is all about handing video feeds and the like. You can read all about
# the CV2 library here: https://opencv.org/
# You cannot run this in COLAB without a lot of re-writing or Jupyter Notebooks reliably.
# Best to use pycharm (install on your laptop)
# You will need to install the cv2 and mediaPipe packages to make this work. You can do this
# by going to
# This one presents you with some data when you pinch your index finger to your thumb
# moves, the data around while you are pinched and drops it when you un pinch.
# It gets the relative positions of your index finger and thump end points to work out if
# you are pinched.

# One thing to remember (or learn) is that the colour sequence is the revers of RGB so is BGR, you get
# odd results if you neglect this and set things up RGB style!!!!!!!

# Get all the libraries - not that many but very powerful they are:
import cv2
import mediapipe as mp
import time
import numpy as np
import math

# Now a few variables for drawing TEXT on the image masks (layers)
font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (10,200)
fontScale              = 2
fontColor              = (255,0,0)
thickness              = 2
lineType               = 1

# Now some constants and variables used to manage the hand landmarks
THUMB_TIP = 4
INDEX_FINGER_TIP = 8


# Now a load of variables that control features of this version of the code.
# These are used to count the number of frames that must pass as the machine moves into and out
# of a pinch move.
# Now for the process settings . These control the state machine that draws things with multiple pinches.
# I.E. when you pinch to start a circle and drag to draw the outer rim.

NOTHING = 0                     # Nothing in process if we are in the process of something it will be non 0.



PINCHGAP = 20                   # The maximum number of pixels between thump tip and first finger
                                # tip below which a PINCH is detected
OPENCOUNTSTART = 3              # The number of frames of open pinch needed to start a pinch.
CLOSEDCOUNT = 3                 # The number of continuous frames of closed count for a valid pinch.
OPENCOUNTEND = 10               # The number of frames open that must occur to end a pinch.
pOpen = False                    # State machine flag set true when open condition is met each loop
pClosed = False                  # State machine flag set true when closed condition is met each loop
rPinch = False                   # State machine that confirms pinch is valid after processing
rOpen = False                    # State machine flag set true when open condition is met after OPENCOUNTSTART or
                                 # OPENCOUNTEND frames
rClosed = False                  # State machine flag set true when closed condition is met after CLOSEDCOUNTFRAMES

rPick = False
rGrab = False
rProcess = NOTHING
rDrop = False
cPinch = False                  # If we have just pinched ona  control set this flag so nothing else happens this loop

PICKMODE = 0                    # The control codes.
CIRCLEMODE = 1                  # Drawing circles
RECTANGLEMODE = 2               # Draw a rectangle
FREEDRAWMODE = 3                # Draw freehand

BEGIN = 1
RADIUSSET = 2
DIAGSET = 3

controlSelected = PICKMODE      # This is the first drawing mode that is selected.
cMode = BEGIN


pPinchDrop = False              # State machine flag that confirms a pinch drop has occurred
xCoordC = 0                     # Holding place for pinch start coordinates.
yCoordC = 0
radius = 0

framesOpenCount = 0             # Now many continuous open pinch frames have we seen
framesClosedCount = 0           # How many continuous closed pinch frames have we seen

pinchDist = 20                  # The pixel distance between nodes 4 & 8 global variable

pinchCenterX = 0                # This is the holding place for the center of the pinch
pinchCenterY = 0                # It will be used as the drop point and is updated at each frame While the closed
                                # variable is True.

rX = 0                          # Pick point offset in object.
rY = 0

HANDSON = False

# Now the moveable squares parameters
RECTSIZEX = 80
RECTSIZEY = 80
XCOORD = 0
YCOORD = 1
BLUE = 2
GREEN = 3
RED = 4
SHAPE = 5
TEXT = 6

FILLED = -1

# Now lets grab a stream from a CAMERA.
cap = cv2.VideoCapture(0)   # You will need to find out which of your cameras is which just play with the number.

# Get the width and height of the video image so we can scale stuff later.
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
# print("Width = ",width," Height = ",height)

# Call up the hands recogniser and supporting tools.
mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

# In this version we will add a mask view where we can draw over the video with
# anything we want and pick up our hand gestures.
ret, mask = cap.read()         # Read the frame
mask = np.zeros_like(mask)     # Clear the mask
# Now I will create a second dataMask 'Overlay' which can display the object list.
ret1, overlay = cap.read()            # Grab the frame
overlay = np.zeros_like(overlay)      # Clear the mask so now we have blank screen.
# Now I will create a second dataMask 'Overlay' which can display the object list.
ret2, controls = cap.read()            # Grab the frame
controls = np.zeros_like(controls)      # Clear the mask so now we have blank screen.

# overlay.size

pinched = False             # So we start with  no pinch.
pinchedHistory = pinched    # Set the history up. We need to track this so we
                            # can see the start and end of a pinch.

# Now our function definitions:#

def drawControls(index):
    ptr = 0
    for ob in controlList:
        cv2.rectangle(controls, (ob[XCOORD], ob[YCOORD]), (ob[XCOORD] + RECTSIZEX, ob[YCOORD] + RECTSIZEY),
                      (ob[BLUE], ob[GREEN], ob[RED]), FILLED)  # A filled rectangle
        if ptr == index:
            cv2.rectangle(controls, (ob[XCOORD], ob[YCOORD]), (ob[XCOORD] + RECTSIZEX, ob[YCOORD] + RECTSIZEY),
                          (255, 255, 0), 1)
        ptr=ptr+1

# Just the one to calculate the distance between two points on the screen.
#
def pinch(fx,fy,tx,ty):
    # Measure the distance between finger and thumb.
    # Returns distance between node points 4 and 8
    # distance =√((x2 – x1)² + (y2 – y1)²).
    # In python that looks like this:
    d = math.sqrt(((fx-tx)**2)+((fy-ty)**2))
    # Return the distance.
    return d

# This function searches through the object list to see if the pinch point (x,y) is within the boundary of one of the
# Objects, If it is it returns the index of the object otherwise -1. It also conditions the rX and rY globals
# which carry the X and Y offsets of the pinch point from the base point of the object.
def objectFound(x,y):
    # Search through our list of objects.
    index = 0
    out = -1
    global objectList, rX, rY
    for ob in objectList:
        # cv2.rectangle(overlay, (ob[0], ob[1]), (ob[0] + w, ob[1] + h), (ob[2], ob[3], ob[4]), -1)  # A filled rectangle
        if x>ob[XCOORD] and x<(ob[XCOORD]+RECTSIZEX) and y>ob[YCOORD] and y<(ob[YCOORD]+RECTSIZEY):
            out = index                     # Which object do we have
            rX = x - ob[XCOORD]             # The point in the object where the pinch center is.
            rY = y - ob[YCOORD]             # The point in the object where the pinch center is
            # print("Found object", index)
        # index it onwards
        index = index + 1
    return out

def controlFound(x,y):
    # Search through our list of objects.
    index = 0
    out = -1
    global objectList, rX, rY
    for ob in controlList:
        if x > ob[XCOORD] and x < (ob[XCOORD] + RECTSIZEX) and y > ob[YCOORD] and y < (ob[YCOORD] + RECTSIZEY):
            out = index  # Which object do we have
            rX = x - ob[XCOORD]  # The point in the object where the pinch center is.
            rY = y - ob[YCOORD]  # The point in the object where the pinch center is
            print("Found object", index)
        # index it onwards
        index = index + 1
    return out

def drawFixedObjects():
    font = cv2.FONT_HERSHEY_SIMPLEX
    for ob in objectList:
        cv2.rectangle(overlay, (ob[XCOORD], ob[YCOORD]), (ob[XCOORD] + RECTSIZEX, ob[YCOORD] + RECTSIZEY),
                      (ob[BLUE], ob[GREEN], ob[RED]), FILLED)  # A filled rectangle

        cv2.putText(overlay, str(ob[TEXT]), (ob[XCOORD]+10, ob[YCOORD]+70), font, 3, (255, 255, 255), 2, cv2.LINE_AA)

def drawNandCGrid():
    cv2.line(mask, (200, 100), (200, 400), (255, 255, 0), 2)
    cv2.line(mask, (300, 100), (300, 400), (255, 255, 0), 2)
    cv2.line(mask, (100, 200), (400, 200), (255, 255, 0), 2)
    cv2.line(mask, (100, 300), (400, 300), (255, 255, 0), 2)

def drawCircle(layer,x,y,rad, blue,green,red):
    cv2.circle(layer,(x,y), rad, (blue,green,red), 2)


# Now the main program.

controlList = [[50,350,200,0,0,10,"X"], [160,350,200,0,0,10,"X"], [270,350,200,0,0,10,"O"],[380,350,200,0,0,10,"O"],[490,350,200,0,0,10,"O"]]
objectList = [[220,20,0,0,200,1,"O"],[320,20,200,0,0,1,"X"],[420,20,0,0,200,1,"O"],[520,20,0,0,200,1,"O"], [420,120,0,0,200,1,"O"],
              [520,120,0,0,200,1,"O"],[420,220,200,0,0,1,"X"],[520,220,200,0,0,1,"X"],[420,320,200,0,0,1,"X"], [520,320,200,0,0,1,"X"]]

for ob in objectList:
    cv2.rectangle(overlay, (ob[XCOORD], ob[YCOORD]), (ob[XCOORD]+RECTSIZEX, ob[YCOORD]+RECTSIZEY), (ob[BLUE], ob[GREEN], ob[RED]), FILLED)  # A filled rectangle

alpha = 0.01  # Transparency factor - so we can see through it.
# Now make the whole drawing in the overlay somewhat transparent.
dataMask = cv2.addWeighted(overlay, alpha, mask, 1 - alpha, 0)

lastDropX = 0
lastDropY = 0

# drawMode = CIRCLES

# Now all the setup stuff
# drawControls(PICKMODE)
drawNandCGrid()

# Now our super loop (while forever)
while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    # print(results.multi_hand_landmarks)
    # Now draw the fixed objects

    drawFixedObjects()

    if results.multi_hand_landmarks:
        if HANDSON:
            for handLms in results.multi_hand_landmarks:
                mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

        # Now if we have any multi hand land marks then we need to draw circles on but into the
        # persistent mask.
        # This code is a refactoring fo the code in the previous blocks
        shape = img.shape
        #print(results.multi_hand_landmarks[1].landmark[0].x)
        # In this version we only allow picking with one hand - two hands in much more complex.
        fingerX = int(results.multi_hand_landmarks[0].landmark[INDEX_FINGER_TIP].x*shape[1])
        fingerY = int(results.multi_hand_landmarks[0].landmark[INDEX_FINGER_TIP].y*shape[0])
        thumbX = int(results.multi_hand_landmarks[0].landmark[THUMB_TIP].x * shape[1])
        thumbY = int(results.multi_hand_landmarks[0].landmark[THUMB_TIP].y * shape[0])

        # SO now we check to see if the two points are within PINCHGAP pixcels of one another.
        # really we should  scale this but for now this seems to work.
        if pinch(fingerX,fingerY,thumbX,thumbY) < PINCHGAP:
            pOpen = False
            pClosed = True
            xCoord = int(fingerX + ((fingerX - thumbX) * -.5))
            yCoord = int(fingerY + ((fingerY - thumbY) * -.5))
            # print("Pinch Spotted")
        else:
            pOpen = True
            pClosed = False

        # Now lets manage the main statemachine - has four states, open pinch = the fingers have been
        # over the pinch distance apart for more than OPENCOUNTSTART frames
        if pOpen:
            framesOpenCount = framesOpenCount+1
            if framesOpenCount > OPENCOUNTSTART:
                rOpen = True                # Looks like we have enough frames to confirm open
                framesClosedCount = 0       # We can reset the framesClosedCount back to 0
                if rClosed:                 # We have moved from closed to open as the last valid was clsoed.
                    rDrop = True            # We have had a drop event
                    rPick = False
                    # print("Drop set")
                    rClosed = False         # We can clear the last rClosed event
        if pClosed:
            framesClosedCount = framesClosedCount+1
            if framesClosedCount > CLOSEDCOUNT:
                rClosed = True              # Looks like we have enough frames to confirm open
                framesOpenCount = 0         # We can reset the framesClosedCount back to 0
                if rOpen:                   # We have moved from open to closed.
                    rPick = True            # We have had a pick event
                    cPinch = True
                    rOpen = False           # We can clear the last rClosed event


        if rPick and not rGrab:                    # We have a pick but nothing grabbed
            # Are we over a moveable object.
            # Find the object
            # Let's see if there is anything here we can grab!
            # So call the object detector with the coordinates of the pinch
            objectNumber = objectFound(xCoord,yCoord)
            if  objectNumber!= -1:
                # We need to pick it up and start moving it.
                rGrab = True    # Set the flag
                print("Found Object")



        if rPick and rGrab and rProcess == NOTHING and controlSelected == PICKMODE:                    # We have a pick and an object grabbed
            # So we have an object

            # First move it in the object list then let the list regen at the next frame
            # we need to modify the two coordinates but without forgetting the rX and rY offsets
            objectList[objectNumber][XCOORD] = xCoord - rX
            objectList[objectNumber][YCOORD] = yCoord - rY

        if rPick and cPinch:
            # print("We are picked and pinched", controlSelected)

            if controlSelected == CIRCLEMODE:
                if cMode == RADIUSSET:      # We are wanting to draw the circle at this radius
                    radius = int(pinch(xCoordC,yCoordC,xCoord,yCoord))
                    drawCircle(overlay,xCoordC,yCoordC,radius, 255,255,0)
                if cMode == BEGIN:          # We are going to call this point the center point.
                    xCoordC = xCoord
                    yCoordC = yCoord
                    cMode = RADIUSSET

            if controlSelected == FREEDRAWMODE:
                if cMode == RADIUSSET:      # We are wanting to draw the circle at this radius
                    radius = int(pinch(xCoordC,yCoordC,xCoord,yCoord))
                    cv2.line(overlay,(xCoordC,yCoordC),(xCoord,yCoord), (255,255,0),2)
                if cMode == BEGIN:          # We are going to call this point the center point.
                    xCoordC = xCoord
                    yCoordC = yCoord
                    cMode = RADIUSSET

        if rDrop and rProcess == NOTHING:   # Now use the rdrop flag if there is no ongoing process
                                            # Processes might include drawing a rectangle by dropping
            # Calculate drop coordinates
            if controlSelected == CIRCLEMODE and cMode == RADIUSSET:   # We can drop the outercircle here into the mask
                drawCircle(mask, xCoordC, yCoordC, radius, 255, 255, 0)
                cMode = BEGIN

            if controlSelected == FREEDRAWMODE and cMode == RADIUSSET:  # We can drop the outercircle here into the mask
                cv2.line(mask,(xCoordC,yCoordC),(xCoord,yCoord), (255,255,0),2)
                cMode = BEGIN

            #if drawMode == CIRCLES:
            #    print("Circle drop actioned @ ",xCoord,",",yCoord)
            #    cv2.circle(mask, (xCoord, yCoord),
             #              radius=10, color=(0, 0, 255), thickness=1)

            #if drawMode == LINES:
            #    print("Line drop actioned @ ", xCoord, ",", yCoord)
             #   cv2.circle(mask, (xCoord, yCoord),
            #               radius=10, color=(0, 0, 255), thickness=1)

            rDrop = False      # We can turn of the pinch drop so the cycle can start again.
            rGrab = False      # Turn off the Grab as well because we have dropped.
            cPinch = False      # Drop out of any drawing mode we might be in
            cMode = BEGIN       # And reset drawing state machine.

    # Now add the masks & Overlays to the main image
    # Overlay has the pickable objects
    # Mask has the drawn objects
    img2 = cv2.add(img, mask)
    img2 = cv2.add(img2,overlay)
    img2 = cv2.add(img2, controls)
    # And show them both but as we are drawing on the screen in reverse
    # lets flip the image over to make drawing simpler.
    img2 = cv2.flip(img2, 1)
    cv2.imshow("Image", img2)
    # Clean the dynamic frame.
    overlay = np.zeros_like(overlay)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    # Now updated the pinched History

    pinchedHistory = pinched
    lastClosed = rClosed
    lastOpen = rOpen

cv2.destroyAllWindows()     # Close all the windows
cap.release()               # Hand back the camera.
