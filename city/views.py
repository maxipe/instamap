from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django import forms
from django.http import JsonResponse

from models import Coordinate, Photo
from django.views.decorators.csrf import csrf_exempt #fixme Workaround

import requests

import time
import threading
import random

import geopy.distance

@csrf_exempt
def index(request):

    return render(request, 'index.html', {})

def findCoordinate(cityName):
    try:
        mapRequest = requests.get('http://maps.googleapis.com/maps/api/geocode/json?address='+cityName)
    except:
        return None

    cityJson = mapRequest.json()

    if not cityJson["results"]:
        return None

    coordinate = Coordinate()
    coordinate.latitude = cityJson["results"][0]["geometry"]["location"]["lat"]
    coordinate.longitude = cityJson["results"][0]["geometry"]["location"]["lng"]
    return coordinate

def makeRequest(photos, coordinate, startTimestamp, finishTimestamp):
    """ Makes request, creates Photos and adds them to photos. """
    photosRequest = requests.get('https://api.instagram.com/v1/media/search?lat='+str(coordinate.latitude)+'&lng='+str(coordinate.longitude)+'&client_id=9e52d8b3795446fd82fe701eebe681f9&distance=5000&count=200&min_timestamp='+str(startTimestamp)+'&max_timestamp='+str(finishTimestamp))
    photosJson = photosRequest.json()
    for photoData in photosJson["data"]:
        location = photoData["location"]
        coordinate = Coordinate()
        coordinate.latitude = location["latitude"]
        coordinate.longitude = location["longitude"]

        photo = Photo()
        photo.coordinate = coordinate
        photo.link = photoData["link"]

        photos.append(photo)

def getCurrentDayInitTime(todayTime):
    """ Returns the time of the start of
    the day of the time recieved."""
    string = str(todayTime.tm_year)
    string += " "+str(todayTime.tm_mon)
    string += " "+str(todayTime.tm_mday)
    string += " 00:00:00"

    return time.strptime(string, "%Y %m %d %H:%M:%S")

def findPhotos(coordinate, initialHour=0, finalHour=24):
    """ Returns list of photos. """
    DAYS_TO_RETRIVE = 7
    #DAYS_TO_RETRIVE = 1
    photos = []
    nowTimeStruct = time.localtime()
    now = int(time.mktime(nowTimeStruct))

    currentDayInitTime = getCurrentDayInitTime(nowTimeStruct)
    currentDayInitTime = time.mktime(currentDayInitTime)

    dayStart = currentDayInitTime - 60*60*24*DAYS_TO_RETRIVE + 60*60*initialHour
    dayEnd = dayStart + 60*60*(finalHour-initialHour)

    startTimestamp = dayStart
    sixHours = 60*60*6
    finishTimestamp = startTimestamp

    intervals = []

    while startTimestamp < now:
        finishTimestamp = startTimestamp + sixHours
        if finishTimestamp > now:
            finishTimestamp = now
            intervals.append((startTimestamp, finishTimestamp))
            break
        elif finishTimestamp > dayEnd:
            finishTimestamp = dayEnd
            intervals.append((startTimestamp, finishTimestamp))
            dayStart += 60*60*24
            dayEnd = dayStart + 60*60*(finalHour-initialHour)
            startTimestamp = dayStart
            finishTimestamp = startTimestamp
        else:
            intervals.append((startTimestamp, finishTimestamp))
            startTimestamp += sixHours

    threads = []
    for start, end in intervals:
        #print time.ctime(start)
        #print time.ctime(end)
        t = threading.Thread(target=makeRequest, args = (photos, coordinate, start, end) )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    if not photos: raise Exception("Empty photosCoordinates")

    #print "Photos #: " + str(len(photos)) + "."

    return photos

def createPoints(coordinate):
    """ Creates a list made of tuples (Coordinate, []).
    The coordinates are created on a grid starting from
    (-DISTANCE,-DISTANCE) to (DISTANCE,DISTANCE) from
    the given coordinate. """
    DISTANCE = 4 # 4000 meters to each side.
    POINT_DISTANCE = 0.100 # Points 250m from each other.

    points = [] # [ (coordinate,[photos]), (), ... ]

    gc = geopy.distance.great_circle()

    center = geopy.distance.Point(coordinate.latitude, coordinate.longitude)
    #print "Center "+str(center)

    # We start finding the top left point
    currentPoint = gc.destination(center, 135, (2*(DISTANCE**2))**0.5)
    #print gc.measure(currentPoint, center)
    for x in xrange(int(2*DISTANCE/POINT_DISTANCE)):
        currentPoint = gc.destination(currentPoint, 90, -POINT_DISTANCE)
        for y in xrange(int(2*DISTANCE/POINT_DISTANCE)):
            p = gc.destination(currentPoint, 0, y*POINT_DISTANCE)
            coord = Coordinate()
            coord.latitude = p[0]
            coord.longitude = p[1]
            points.append( (coord,[]) )
            #print gc.measure(p, center)
        #print " --- "

    return points

def putPhotosInPoints(photos, points):
    DISTANCE_LIMIT = 0.100 # 100m
    gc = geopy.distance.great_circle()

    alreadyExistingCoordinates = {} #to avoid default coordinates
    for photo in photos:

        photoPoint = geopy.distance.Point(
            photo.coordinate.latitude,
            photo.coordinate.longitude
        )


        key = str(photoPoint.latitude)+str(photoPoint.longitude)
        if key in alreadyExistingCoordinates:
            continue
        alreadyExistingCoordinates[key] = photo

        for point in points:
            pointPoint = geopy.distance.Point(
                point[0].latitude,
                point[0].longitude
            )
            if gc.measure(photoPoint, pointPoint) < DISTANCE_LIMIT:
                #print "appended"
                point[1].append(photo)

                #print gc.measure(photoPoint, pointPoint)
                #print photoPoint
                #print pointPoint
                #return

    return

def comparePoints(p1,p2):
    """ p1 and p2 are tuples of (Coordinate, [])
        Returns:
        -1 if p1 list longer than p2.
        1 if p2 list longer than p1.
        0 if equal length. """

    return cmp( len(p2[1]) ,len(p1[1]) )

#fixme: workaround
@csrf_exempt
def getCityInfo(request):
    if not request.POST["city-name"]:
        return redirect('/')

    try:
        if request.POST["initial-time"]:
            initialHour = int(request.POST["initial-time"])
        if request.POST["final-time"]:
            finalHour = int(request.POST["final-time"])
        if initialHour > finalHour or initialHour < 0 or finalHour > 24:
            raise ValueError
    except:
        print "Invalid time."
        initialHour = 0
        finalHour = 24



    cityName = request.POST["city-name"]
    coordinate = findCoordinate(cityName)
    if not coordinate:
        return redirect('/')

    photos = findPhotos(coordinate, initialHour, finalHour)

    points = createPoints(coordinate)

    putPhotosInPoints(photos, points)
    points = sorted(points, cmp=comparePoints)
    photoTuples = []
    photoSets = []
    photoAlbums = [] # [ (#ofAlbum, [link1, link2]) ]

    for x in xrange(20):
        try:
            photoAlbums.append((x+1, []))
            for photo in points[x][1]:
                photoAlbums[x][1].append(photo.link)
            photo = random.choice(points[x][1])
            photoTuples.append( (photo.coordinate.latitude, photo.coordinate.longitude, "#"+str(x+1)) )

        except:
            break

    return render(
        request, 'index.html',
        {
            'coordinate':coordinate,
            'cityName':cityName,
            'photoTuples': photoTuples,
            'photoAlbums': photoAlbums,
            'initialHour': initialHour,
            'finalHour': finalHour
        }
    )
