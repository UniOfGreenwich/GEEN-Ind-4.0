## GEEN1191 Industry 4.0 Code fragments.

This repository contains all the code fragements for GEEN1191 Industry 4.0 lab experiments and project work.

There are a number of experimental software items here:

### Augmented Reality fragments

These are all examples of systems of systems because we are relying on systems from 3rd party’s we have no control over. OpenCV (which we sort of could have some control as it is an open source project) and mediapipe which is a Google machine learning model over which only Google has control.

SimpleHandsDoodle.py  This is a python coded application of mediapipe and OpenCV it uses your camera to project an image and shows the hand landmarks model works. Once it it working it will draw small circles at the tip of your first finger(s) as you move them about in the video stream. You may need to change the camera number if you have more than one on your system!!!!

DragandDoodle.py  This is a python coded application again using OpenCV and media pipe. It does not show the landmarks and uses a simple algorithm to work out when you pinch your thumb and first finger together. It has some controls at the bottom of the screen (backwards because the screen is inverted to help you navigate in front of the camera) P = pick - allows you to grab the blocks at the top by pinching and move them around, L = Line - allows you to pinch and drag a line out. C = Circle - allows you to pinch the center point and then drag out the radius of a circle. Feel free to add other controls.

NandC.py  This is a python coded application again using OpenCV and media pipe. It does not show the landmarks and uses a simple algorithm to work out when you pinch your thumb and first finger together and drag the O and X rectangles into the game frame. It does not announce the winner. See if you can think of ways of adding that feature.


