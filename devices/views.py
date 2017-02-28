import time
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Device
from .s20control import orviboS20
import json


def validate_request(request, method='POST'):
    if 'API_KEY' in request.POST and method == 'POST':
        if str(settings.API_KEY) == str(request.POST['API_KEY']):
            return True
    elif 'API_KEY' in request.GET and method == 'GET':
        if str(settings.API_KEY) == str(request.POST['API_KEY']):
            return True
    print "[INFO] BAD API KEY"
    return False


def device_actuator(device_id, state=True):
    try:
        device = Device.objects.get(pk=device_id)
        control = orviboS20()
        if state is True:
            control.poweron(device.ip_address, device.mac)
        elif state is False:
            control.poweroff(device.ip_address, device.mac)
    except:
        print '[ERROR] Failed to change device state'
        pass


@csrf_exempt
def poweroff(request, device=None):
    if validate_request(request):
        device_actuator(device, False)
    else:
        print "[ERROR] Validation Failed"
    return HttpResponse('ok')


@csrf_exempt
def poweron(request, device=None):
    if validate_request(request):
        device_actuator(device, True)
    return HttpResponse('ok')


def status(request, device=None):
    if validate_request(request, 'GET'):
        device_actuator(device, True)
    return HttpResponse('ok')
