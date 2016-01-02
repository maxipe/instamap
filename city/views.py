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

from quadtree import QuadTree, Block, Point

@csrf_exempt
def index(request):
    form = forms.CharField(label='City', max_length=100)

    #return HttpResponse("Hello world! -")
    return render(request, 'index.html', {'form':form})

def makeRequest(photos, coordinate, startTimestamp, finishTimestamp):

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

    #for coord in photosCoordinates:

    # Arreglar: Guardar objetos Photo en la lista, asi puedo hacer todo como un humano normal. Pasar quadtree a models.py
    # Analizar: Poner de limite al Quadtree la minima y maxima latitud/longitud posible.

    #print str(len(photosJson["data"])) + " ASD"
    print "Cantidad de fotos: " + str(len(photos)) + "."

    return photos


#fixme: workaround
@csrf_exempt
def getCityInfo(request):

    if not request.POST["city-name"]:
        return redirect('/')

    cityName = request.POST["city-name"]
    mapRequest = requests.get('http://maps.googleapis.com/maps/api/geocode/json?address='+cityName)
    cityJson = mapRequest.json()

    if not cityJson["results"]:
        return redirect('/')
    #print cityJson["results"][0]["geometry"]["location"]

    coordinate = Coordinate()
    coordinate.latitude = cityJson["results"][0]["geometry"]["location"]["lat"]
    coordinate.longitude = cityJson["results"][0]["geometry"]["location"]["lng"]

    photos = findPhotos(coordinate)
    amountOfPhotos = len(photos)

    totalDistance = 0
    #photosWithDistances = [] #contains list [distance,photo]
    for x in xrange(amountOfPhotos):
        photo = photos[x]
        #photosWithDistances.append([0,photo])

        for y in xrange(x+1,amountOfPhotos):
            distance = photo.distance(photos[y])
            totalDistance += distance
            #photosWithDistances[x][0] += distance
            #photosWithDistances[y][0] += distance

    averageDistance = (totalDistance*1.0) / amountOfPhotos
    photosWithAmountOfCloseNeightbours = [] #(neightbours, photo)

    for photo in photos:
        amountOfPhotosNearerThanTheAverage = 0
        for otherPhoto in photos:
            if photo == otherPhoto: continue
            if photo.distance(otherPhoto) < averageDistance:
                amountOfPhotosNearerThanTheAverage += 1



    #photosWithDistances.sort()

    photoTuples = []
    for photo in photos:
        photoTuples.append( (photo.coordinate.latitude, photo.coordinate.longitude, photo.link) )

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
