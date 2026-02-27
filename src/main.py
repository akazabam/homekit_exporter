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

    def _readConfig(self):
        with open(self.confFile, 'r') as file:
            return yaml.safe_load(file)

    def getDeviceInfo(self, device):
        encDevice = quote(device)
        DeviceUrl = f'http://{self.host}:{self.port}/info/{encDevice}'
        try:
            r = self.req.get(DeviceUrl)
            r.raise_for_status()
        except HTTPError as httpErr:
            return {'error': httpErr}
        except Exception as err:
            return {'error': err}

        return r.json()

    def getAllDeviceMetrics(self):
        metrics = {}
        for device in self.confData['devices']:
            jsonOut = self.getDeviceInfo(device)
            if 'error' in jsonOut:
                error = jsonOut['error']
                print(f'WARNING: {device} info check returned: {error}')
                continue
            name      = jsonOut['name']
            room      = jsonOut['room']
            reachable = jsonOut['reachable']
            type      = jsonOut['type']
            metricsStr = f'homekit_{type}_{room}_{name}'.lower().replace(" ", "")

            metrics[f'{metricsStr}_reachable'] = reachable
            self.metricsDesc[f'{metricsStr}_reachable'] = f'Reachable metric for device {device}'

            for metric, value in jsonOut['state'].items():
                if isinstance(value, str):
                #    metric = f'state_{value}'
                #    value  = 1
                     continue
                m = f'{metricsStr}_{metric}'
                if 'temperature' in metric.lower():
                    if self.temperature.lower() == 'f':
                        value = (value * 9/5) + 32
                metrics[m] = value
                if m not in self.metricsDesc:
                    self.metricsDesc[m] = f'{metric.capitalize()} metric for device {device}'
        return metrics

    def getPollTime(self):
        return self.pollTime

    def getMetricsDescriptions(self):
        return self.metricsDesc

if __name__ == '__main__':
    exit(main())
