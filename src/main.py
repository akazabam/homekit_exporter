#!/usr/local/bin/python3

import requests
import signal
import sys
import time
import yaml

from prometheus_client import start_http_server, Gauge
from requests.exceptions import HTTPError
from urllib.parse import quote, quote_plus

def main():
    signal.signal(signal.SIGTERM, shutdownHandler)
    signal.signal(signal.SIGINT, shutdownHandler)

    h = HomeKit('homekit_exporter.yaml')
    metrics = {}
    homekitMetrics = h.getAllDeviceMetrics()
    homekitMetricsDesc = h.getMetricsDescriptions()
    for metric, value in homekitMetrics.items():
        metrics[metric] = Gauge(metric, f'{homekitMetricsDesc[metric]}')

    start_http_server(8000)

    while True:
        try:
            for metric, value in h.getAllDeviceMetrics().items():
                metrics[metric].set(value)
            time.sleep(h.getPollTime())
        except Exception as err:
            print(err)

def shutdownHandler(signum, frame):
    print(f'Received {signum}. Shutting down.')
    sys.exit(0)

def getNestedValue(obj, *path, default=None):
    for index in path:
        try:
            obj = obj[index]
        except:
            print(f'WARNING: "{index}" does not exist. Using default config option: {default}')
            return default
    return obj

class HomeKit:
    def __init__(self, confFile):
        self.confFile    = confFile
        self.confData    = self._readConfig()
        self.host        = getNestedValue(self.confData, 'connection', 'host', default='localhost')
        self.port        = getNestedValue(self.confData, 'connection', 'port', default=8423)
        self.pollTime    = getNestedValue(self.confData, 'settings', 'poll', default=30)
        self.temperature = getNestedValue(self.confData, 'settings', 'temperature', default='F')
        self.req         = requests.Session()
        self.metricsDesc = {}
        self.rooms       = {}

    def _readConfig(self):
        with open(self.confFile, 'r') as file:
            return yaml.safe_load(file)

    def getRooms(self):
        roomsUrl = f'http://{self.host}:{self.port}/list/rooms'
        try:
            r = self.req.get(roomsUrl)
        except HTTPError as httpErr:
            return {'error': httpErr}
        except Exception as err:
            return {'error': err}

        for roomDict in r.json():
            room = roomDict['name']
            if room not in self.rooms:
                self.rooms[room] = HomeKitRoom(self, room)

    def getAllDeviceMetrics(self):
        self.getRooms()

        devices = []
        for room, r in self.rooms.items():
            devices.extend(r.getDevices())
            
        metrics = {}
        for device in devices:
            if 'error' in device:
                error = device['error']
                print(f'WARNING: {device} info check returned: {error}')
                continue
            name       = ''.join(e for e in device['name'] if e.isalnum())
            room       = ''.join(e for e in device['room'] if e.isalnum())
            reachable  = device['reachable']
            type       = device['type']
            metricsStr = f'homekit_{type}_{room}_{name}'.lower()

            metrics[f'{metricsStr}_reachable'] = reachable
            self.metricsDesc[f'{metricsStr}_reachable'] = f'Reachable metric for device {room}/{name}'

            if 'state' not in device:
                continue
            for metric, value in device['state'].items():
                if isinstance(value, str):
                     # Can't handle strings right now
                     continue
                m = f'{metricsStr}_{metric}'
                if 'temperature' in metric.lower():
                    if self.temperature.lower() == 'f':
                        value = (value * 9/5) + 32
                metrics[m] = value
                if m not in self.metricsDesc:
                    self.metricsDesc[m] = f'{metric.capitalize()} metric for device {room}/{name}'
        return metrics

    def getPollTime(self):
        return self.pollTime

    def getMetricsDescriptions(self):
        return self.metricsDesc

class HomeKitRoom:
    def __init__(self, h, room):
        self.h       = h
        self.room    = room

    def getDevices(self):
        encRoom = quote(self.room)
        DeviceUrl = f'http://{self.h.host}:{self.h.port}/info/{encRoom}'
        try:
            r = self.h.req.get(DeviceUrl)
            r.raise_for_status()
        except HTTPError as httpErr:
            return {'error': httpErr}
        except Exception as err:
            return {'error': err}

        return r.json()

if __name__ == '__main__':
    exit(main())
