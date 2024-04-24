# Here is a simple start to making AR a thing Mike Sharp March 2024.
# All these code samples are VERY CRUDE, but they will give you a good idea
# of how easy it is to create 'AR' content in code.
# It uses the two big libraries and associated connections:
# Google mediapipe library which has a vast array of pre-trained
# algorithms and we will just use the one for hands. You can learn a lot more
# about mediapipe here: https://learnopencv.com/introduction-to-mediapipe/
# The CV2 library is all about handing video feeds and the like. You can read all about
# the CV2 library here: https://opencv.org/
# You cannot run this in COLAB without a lot of re-writing or Jupyter Notebooks reliably.
# Best to use pycharm (install on your laptop)
# You will need to install the cv2 and mediaPipe packages to make this work. You can do this
# by going to https://pypi.org/project/opencv-python/ and https://pypi.org/project/mediapipe/

# This project is also an excellent example of the systems of systems conundrum. We are using
# Google and OPENCV systems to create our AR world and because we have no control of these tools
# we have to be aware that they could change at any time and render our project here unusable!

# This version of the code leaves a trail of circles where ever your index finger end travels!
# It could be much clever and join the dots, but you will get the point!
# You need to understand have we use masks (Additional layers of the image if you like).
    # We grab an image, zero all the pixels (turn them black), then draw on the mask and then add the mask
    # to the main image before we show it. This makes the circles persistant (unlike the hand
    # lines and nodes drawn on the live image).

import cv2                      # Get the video & screen drawing library
import mediapipe as mp          # get the hand identification / classification model library
import time                     # In case we need it to do anything with 'time'
import numpy as np              # In case we need it do any number work
import math                     # In case we need it to do any maths!


cap = cv2.VideoCapture(0)   # You will need to find out which of your cameras is which,
                            # ust play with the number, my front camera was 0.

# Call up the hands recogniser and supporting tools.
mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

# In this version we will add a mask view where we can draw over the video with
# anything we want and pick up our hand gestures.
ret, old_frame = cap.read()
mask = np.zeros_like(old_frame)     # Clear the mask

# Now our super loop (while forever)
while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    # print(results.multi_hand_landmarks)

    # Now if we have results we will draw on all the nodes and links.
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

    # Now if we have any results then we need to draw circles on but into the
    # persistent mask we created above.
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:

            g = 0   # Now keep track of which landmark I want to draw with
                    # It is actually 8 as this is tip of our index finger.
            for landmark in handLms.landmark:
                x = landmark.x
                y = landmark.y

                shape = img.shape
                relative_x = int(x * shape[1])
                relative_y = int(y * shape[0])

                if g==8:        # We have found the tip of the index finger in our list
                    # Draw with just this point (tip of index finger
                    # Let's draw a circle at the tip of index finger.
                    cv2.circle(mask, (relative_x, relative_y),
                               radius=2, color=(255, 255, 255), thickness=1)
                    fingerX = relative_x
                    fingerY = relative_y
                g = g +1

    # Now add the masks to the main image to create a final image to display
    img2 = cv2.add(img, mask)
    # And show them both.
    img2 = cv2.flip(img2,1)
    cv2.imshow("Image", img2)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()     # Close all the windows
cap.release()               # Hand back the camera.