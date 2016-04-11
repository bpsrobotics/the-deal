#!/usr/bin/env python2.7
import cv2
import numpy as np
import sys
import pickle
import time
from multiprocessing import Pool

start = time.time()
serialFile = "/home/solomon/pickle.txt"


# Note: System arguments should take the form of an IP address of the video
# capture feed

# srcImg = cv2.VideoCapture()  # Define srcImg as image/video capture
#
# if len(sys.argv) != 2:
#     print("Error: specify an URL to connect to")
#     exit(0)
#
# url = sys.argv[1]
#
# srcImg.open("http://127.0.0.1:8080/stream.wmv")
# ret, frameImg = srcImg.read()  # Test
# imgY, imgX, imgChannels = frameImg.shape

srcImg = cv2.imread("/home/solomon/frc/the-deal/RealFullField/" +
                    sys.argv[1] + ".jpg", 1)
print ("Read image: " + str(format(time.time() - start, '.5f')))
start = time.time()


def percentFromResolution(srcImg, yTargetRes, xTargetRes):
    imgY, imgX, imgChannels = srcImg.shape
    modPercentX = float(xTargetRes) / imgX
    modPercentY = float(yTargetRes) / imgY
    return [modPercentY, modPercentX]


def imgScale(toScale, percentX, percentY):
    scaledImg = cv2.resize(toScale, None, fx=percentX, fy=percentY,
                           interpolation=cv2.INTER_CUBIC)  # MaybeTry INTER_AREA
    return scaledImg


def threshHSL(imgSrc, lower, upper):
    """Returns binary mask of image based on HSL bounds"""
    imgSrcHLS = cv2.cvtColor(imgSrc, cv2.COLOR_BGR2HLS)
    npLower = np.array([lower[0], lower[2], lower[1]])  # Compesate for HLSvsHSL
    npUpper = np.array([upper[0], upper[2], upper[1]])
    tmp = cv2.inRange(imgSrcHLS, npLower, npUpper)
    return tmp


def threshRGB(imgSrc, lower, upper):
    """Returns binary mask of image based on RGB bounds"""
    imgSrcRGB = cv2.cvtColor(imgSrc, cv2.COLOR_BGR2RGB)
    npLower = np.array([lower[0], lower[1], lower[2]])
    npUpper = np.array([upper[0], upper[1], upper[2]])
    tmp = cv2.inRange(imgSrcRGB, npLower, npUpper)
    return tmp


def cvAdd(img1, img2):
    """Returns addition of 2 images"""
    tmp = cv2.add(img1, img2)
    return tmp


def findContours(img):
    """Finds contours in image, preferably binary image"""
    contours, hierarchy = \
        cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours, hierarchy

print ("function defs: " + str(format(time.time() - start, '.5f')))
start = time.time()

srcImg = imgScale(srcImg, percentFromResolution(srcImg, 240, 320)[0],
                  percentFromResolution(srcImg, 240, 320)[1])
# srcImg = cv2.resize(srcImg, None, fx=.5, fy=.5, interpolation=cv2.INTER_CUBIC)
print ("Scale: " + str(format(time.time() - start, '.5f')))
start = time.time()
srcImg = cv2.GaussianBlur(srcImg, (5, 5), 5)
print ("Blur: " + str(format(time.time() - start, '.5f')))
start = time.time()

a = threshHSL(srcImg, [50, 25, 34], [93, 255, 149])  # HSL thresh lower/upper
print ("HSL: " + str(format(time.time() - start, '.5f')))
start = time.time()
b = threshRGB(srcImg, [110, 119, 126], [255, 255, 255])  # RGB lower/upper
print ("RGB: " + str(format(time.time() - start, '.5f')))
start = time.time()
c = cvAdd(a, b)
print ("Add: " + str(format(time.time() - start, '.5f')))
start = time.time()
d = c
contours, hiearchy = findContours(d)
print ("Contours: " + str(format(time.time() - start, '.5f')))
start = time.time()


tmpVar = 0

while len(contours) > 1:  # this inefficient mess finds the biggest contour
    # (I think)
    for z in range(0, len(contours)):
        try:
            if cv2.contourArea(contours[z]) <= tmpVar:
                contours.pop(z)
        except IndexError:
            break
        # print (str(tmpVar) + ": " + str(len(contours)) + ": " + str(z))
    tmpVar += 1

print ("Found biggest: " + str(format(time.time() - start, '.5f')))
start = time.time()


# rect = cv2.minAreaRect(contours[0])
# box = cv2.cv.BoxPoints(rect)
# box = np.int0(box)
# cv2.drawContours(srcImg, [box], 0, (0, 255, 0), 2)
#
# rows, cols = srcImg.shape[:2]
# [vx, vy, x, y] = cv2.fitLine(contours[0], cv2.cv.CV_DIST_L2, 0, 0.01, 0.01)
# lefty = int((-x*vy/vx) + y)
# righty = int(((cols-x)*vy/vx)+y)
# cv2.line(srcImg, (cols-1, righty), (0, lefty), (255, 0, 0), 2)

hull = cv2.convexHull(contours[0], returnPoints=True)
print ("Convex hull: " + str(format(time.time() - start, '.5f')))
start = time.time()

(count, _, _) = hull.shape
hull.ravel()
hull.shape = (count, 2)


tmpVar = 0
itera = 0
maxIter = 256
iii = len(cv2.approxPolyDP(hull, tmpVar, True))
while iii != 4:
    if iii > 4:
        tmpVar += 1
    elif iii < 4:
        tmpVar -= 1
    itera += 1
    if itera >= maxIter:
        break
    iii = len(cv2.approxPolyDP(hull, tmpVar, True))

approx = cv2.approxPolyDP(hull, tmpVar, True)

print ("Found quadrangle: " + str(format(time.time() - start, '.5f')))
start = time.time()

cv2.drawContours(srcImg, contours, -1, (0, 0, 255), 3)
cv2.polylines(srcImg, np.int32([hull]), True, (0, 255, 0), 5)
cv2.drawContours(srcImg, approx, -1, (0, 255, 0), 3)

for x in range(0, len(approx)):
    # print (x)
    # print (approx[x][0][0])
    cv2.putText(srcImg,
                " " + str(x) + ": (" + str(approx[x][0][0]) +
                ", " + str(approx[x][0][1]) + ")",
                (approx[x][0][0], approx[x][0][1]),
                cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)

print ("Drew image: " + str(format(time.time() - start, '.5f')))
start = time.time()


def imgUntilQ(srcImg):
    cv2.imshow('e', srcImg)
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

cv2.imwrite("processed/" + sys.argv[1] + "-processed.jpg", srcImg)
print ("Wrote image: " + str(format(time.time() - start, '.5f')))
start = time.time()

# Starting to calculate stuff for NT publishing.
# Items to be published:
#   Center of box/contour (maybe avg them)
#   4 points
#   Slopes of angles of sides of box
#   Box height
#   Box width
# Planned output:
# [center, (p1, p2, p3, p4), (Mp1, Mp2, Mp3, Mp4), (height, width)]


p1, p2, p3, p4 = [approx[0][0][0], approx[0][0][1]], \
                 [approx[1][0][0], approx[1][0][1]], \
                 [approx[2][0][0], approx[2][0][1]], \
                 [approx[3][0][0], approx[3][0][1]]
xSize = 0
ySize = 0
pointArr = [p1, p2, p3, p4]

leftPoints = sorted(pointArr)[:2]
rightPoints = sorted(pointArr)[2:]
topPoints = sorted(sorted(pointArr, key=lambda x: x[1])[:2])
bottomPoints = sorted(sorted(pointArr, key=lambda x: x[1])[2:])

xSize = sorted(pointArr)[-1][0] - sorted(pointArr)[0][0]
ySize = sorted(pointArr, key=lambda x: x[1], reverse=True)[0][1] - \
        sorted(pointArr, key=lambda x: x[1])[0][1]

approxMoments = cv2.moments(approx)
contourMoments = cv2.moments(contours[0])
approxCentroidY = int(approxMoments['m01']/approxMoments['m00'])
approxCentroidX = int(approxMoments['m10']/approxMoments['m00'])
cv2.circle(srcImg, (approxCentroidX, approxCentroidY), 5, (255, 0, 255))

# print (p1, p2, p3, p4)

leftSlope, rightSlope, topSlope, bottomSlope = \
    format((leftPoints[1][1] - leftPoints[0][1]) /
           float(leftPoints[1][0] - leftPoints[0][0]), '.2f'),\
    format((rightPoints[1][1] - rightPoints[0][1]) /
           float(rightPoints[1][0] - rightPoints[0][0]), '.2f'),\
    format((topPoints[1][1] - topPoints[0][1]) /
           float(topPoints[1][0] - topPoints[0][0]), '.2f'),\
    format((bottomPoints[1][1] - bottomPoints[0][1]) /
           float(bottomPoints[1][0] - bottomPoints[0][0]), '.2f')

# print (leftPoints[1][1], leftPoints[0][1])
# print (leftPoints[1][0], leftPoints[0][0])
# print (leftSlope, rightSlope, topSlope, bottomSlope)


finalDict = {}

finalDict["approxCentroidX"] = int(approxCentroidX)
finalDict["approxCentroidY"] = int(approxCentroidY)

finalDict["xSize"] = int(xSize)
finalDict["ySize"] = int(ySize)

finalDict["p1"] = (int(p1[0]), int(p1[1]))
finalDict["p2"] = (int(p2[0]), int(p2[1]))
finalDict["p3"] = (int(p3[0]), int(p3[1]))
finalDict["p4"] = (int(p4[0]), int(p4[1]))

finalDict["leftSlope"] = float(leftSlope)
finalDict["rightSlope"] = float(rightSlope)
finalDict["topSlope"] = float(topSlope)
finalDict["bottomSlope"] = float(bottomSlope)
# print (str(leftSlope) + ", " + str(rightSlope) + ", " + str(topSlope) + ", " +
#        str(bottomSlope))

# Side slopes
print ("Made dict: " + str(format(time.time() - start, '.5f')))
start = time.time()

with open(serialFile, 'wb') as j:
    # pickle.dump(finalList, j)
    pickle.dump(finalDict, j, 2)

print ("Dumped pickle: " + str(format(time.time() - start, '.5f')))
start = time.time()
# imgUntilQ(srcImg)