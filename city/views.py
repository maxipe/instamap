from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django import forms
from django.http import JsonResponse

from models import Coordinate
from django.views.decorators.csrf import csrf_exempt #fixme Workaround

import requests

@csrf_exempt
def index(request):
    form = forms.CharField(label='City', max_length=100)

    #return HttpResponse("Hello world! -")
    return render(request, 'index.html', {'form':form})

#fixme: workaround
@csrf_exempt
def getCityInfo(request):

    if not request.POST["city-name"]:
            return redirect('/')

    cityName = request.POST["city-name"]
    r = requests.get('http://maps.googleapis.com/maps/api/geocode/json?address='+cityName)
    cityJson = r.json()

    if not cityJson["results"]:
        return redirect('/')
    #print cityJson["results"][0]["geometry"]["location"]

    coordinate = Coordinate()
    coordinate.latitude = cityJson["results"][0]["geometry"]["location"]["lat"]
    coordinate.longitude = cityJson["results"][0]["geometry"]["location"]["lng"]

    #print request.POST
    #print coordinate.latitude
    return render(request, 'index.html', {'coordinate':coordinate, 'cityName':cityName})
