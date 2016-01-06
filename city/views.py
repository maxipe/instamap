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

import geopy.distance

@csrf_exempt
def index(request):
    form = forms.CharField(label='City', max_length=100)

    #return HttpResponse("Hello world! -")
    return render(request, 'index.html', {'form':form})

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

def findPhotos(coordinate):
    """ Returns list of photos. """
    DAYS_TO_RETRIVE = 7
    #DAYS_TO_RETRIVE = 1
    photos = []
    currentTimestamp = int(time.time())
    startTimestamp = currentTimestamp - 60*60*24*DAYS_TO_RETRIVE
    sixHours = 60*60*6
    finishTimestamp = startTimestamp + sixHours # Gets photos every 6 hours

    threads = []
    while finishTimestamp < currentTimestamp:
        #print "LoopStart"

        t = threading.Thread(target=makeRequest, args = (photos, coordinate, startTimestamp, finishTimestamp) )
        threads.append(t)
        #t.daemon = True
        t.start()


        startTimestamp += sixHours
        finishTimestamp += sixHours

        #print "LoopFinish"

    for t in threads:
        t.join()

    if not photos: raise Exception("Empty photosCoordinates")

    print "Cantidad de fotos: " + str(len(photos)) + "."

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

    cityName = request.POST["city-name"]
    coordinate = findCoordinate(cityName)
    if not coordinate:
        return redirect('/')

    photos = findPhotos(coordinate)

    points = createPoints(coordinate)


    putPhotosInPoints(photos, points)
    points = sorted(points, cmp=comparePoints)
    photoTuples = []
    """
    print "A"
    for x in xrange(10):
        print len(points[x][1])
    print "B"
    for x in xrange(len(points)-10, len(points)):
        print len(points[x][1])
        #photoTuples.append( (points[x][0].latitude, points[x][0].longitude, "") )
    """

    for x in xrange(20):
        for photo in points[x][1]:
            photoTuples.append( (photo.coordinate.latitude, photo.coordinate.longitude, photo.link) )

    """
    x = len(points)-1
    photoTuples.append( (points[x][0].latitude, points[x][0].longitude, "CENTER") )

    z = 0
    dict = {}
    for photo in points[x][1]:
        dict[str(points[x][0].latitude)+str(points[x][0].longitude)] = True
        photoTuples.append( (photo.coordinate.latitude, photo.coordinate.longitude, str(z)) )
        #print "Una foto"
        print "a", str(points[x][0].latitude), str(points[x][0].longitude)
        z += 1

    """

    """
    photoTuples = []
    for photo in photos:
        photoTuples.append( (photo.coordinate.latitude, photo.coordinate.longitude, photo.link) )
    """
    """
    photoTuples = []
    for a in points:
        coordi = a[0]
        photoTuples.append( (coordi.latitude, coordi.longitude, "") )
    """
    #
    #       PENSAR: Refinar haciendo menos Points, y despues dandole
    #       bola a donde haya mas photos.

    #print request.POST
    #print coordinate.latitude
    return render(
        request, 'index.html',
        {
            'coordinate':coordinate,
            'cityName':cityName,
            'photoTuples': photoTuples
        }
    )
