import cv2
import urllib
import numpy as np
import subprocess

WINDOW_NAME = "Pokemon"

def getWindow():
    result = subprocess.check_output(["xdotool", "search", "--name", WINDOW_NAME])
    return result.split("\n")[0]

def fire(keycode):
    subprocess.call(["xdotool", "key", "--window", str(window_id), keycode])

def diffImg(t1, t2):
    gray1 = cv2.cvtColor(t1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(t2, cv2.COLOR_BGR2GRAY)
    d1 = cv2.absdiff(gray1, gray2)
    blurred = cv2.blur(d1, (15, 15))
    return cv2.threshold(blurred,5,255,cv2.THRESH_BINARY)[1]

def processFrame(bytes):
  a = cv2.imdecode(np.fromstring(bytes, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
  return a

def getButtonPress(pos):
  x, y = pos
  if y < height/3:
    if x < width/3:
      return ('z', "B")
    if x > 2*width/3:
      return ('x', "A")
    return ('w', "UP")
  if y > 2*height/3:
    if x < width/3:
      return ('q', "SELECT")
    if x > 2*width/3:
      return ('e', "START")
    return ('s', "DOWN")
  if x < width/3:
    return ('a', "LEFT")
  if x > 2*width/3:
    return ('d', "RIGHT")
  return None, "EMPTY"


height = 480
width = 640
runningAverage = np.zeros((height,width, 3), np.float64) # image to store running avg
stream=urllib.urlopen('***REMOVED***')
bytes=''
areaThreshold = 1000
framecount = 0
window_id = getWindow()


overlay = cv2.imread("overlay2.png", 1)
overlayMask = cv2.cvtColor( overlay, cv2.COLOR_BGR2GRAY )
res, overlayMask = cv2.threshold( overlayMask, 10, 1, cv2.THRESH_BINARY_INV)
h,w = overlayMask.shape
overlayMask = np.repeat( overlayMask, 3).reshape( (h,w,3) )


while True:
    bytes+=stream.read(1024)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:

        img = processFrame(bytes[a:b+2])
        bytes= bytes[b+2:]

        cv2.accumulateWeighted(img, runningAverage, .2, None)

        diff = diffImg(img, runningAverage.astype(np.uint8))

        contours, hierarchy = cv2.findContours(diff, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        contourAreas = {cv2.contourArea(c):c for c in contours}
        if len(contours) != 0:
            maxarea = max(contourAreas.keys())
            if maxarea > areaThreshold:
                largestContour = contourAreas[maxarea]
                ccenter, cradius = cv2.minEnclosingCircle(largestContour)
        contourImg = np.zeros((height,width, 3), np.uint8)
        cv2.circle(contourImg,(int(ccenter[0]), int(ccenter[1])),3,(0,255,255),2)

        if framecount == 10:
          keycode, value = getButtonPress(ccenter)
          print(value)
          if keycode != None:
            fire(keycode)
          framecount = 0

        cv2.line(contourImg, (0, height/3), (width, height/3), (255, 255, 255))
        cv2.line(contourImg, (0, 2*height/3), (width, 2*height/3), (255, 255, 255))
        cv2.line(contourImg, (width/3, 0), (width/3, height), (255, 255, 255))
        cv2.line(contourImg, (2*width/3, 0), (2*width/3, height), (255, 255, 255))

        img *= overlayMask
        img += overlay

        cv2.imshow('i', cv2.add(img, contourImg))

        framecount += 1
        if cv2.waitKey(1) ==27:
            exit(0)
