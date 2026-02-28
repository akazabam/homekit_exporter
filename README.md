# homekit_exporter
This project exports metrics from Apple Home devices using [Itsyhome](https://github.com/nickustinov/itsyhome-macos) with a Prometheus exporter written in Python. It includes a basic Prometheus instance to pull the metrics, and a Grafana instance that can be configured to use metrics.

## Requirements

You will need the following:
* A Mac signed in with your Apple account and Apple Home working (I use an old headless Mac Mini). Presumable you will want it set up to never sleep.
* Docker Desktop
* The Pro version of [Itsyhome](https://github.com/nickustinov/itsyhome-macos)

In Itsyhome, Go to Settings -> Webhooks/CLI -> Enable server. You can stop here, but this will expose the API to your whole network. To prevent this, go to Mac Settings -> Network -> Firewall -> Enable. Then Options -> Add Itsyhome.app if not already present, and block it.

## Exporter Setup

* In a terminal, clone this project.
* If you already have Prometheus and/or Grafana set up, you can remove its configuration from compose.yaml, but this will require extra configuration to use the exporter, which is not covered here.
* In the cloned repo directory, run `docker compose up --build -d`
* Verify the exporter works at http://localhost:8000. You should see a whole list of homekit_ metrics for all devices in all rooms.
* Login to Grafana at http://localhost:3000 and login with admin/admin (You will be prompted to change that).
* Go to Connections -> Data sources -> Add new data source -> Prometheus. Set 'Prometheus server URL' to 'http://localhost:9090'.
* You should now be able to create a new dashboard and browse the homekit_ metrics, which is not covered here.

## Current Limitations

Prometheus can only store numeric data, but Homekit devices can sometimes report metric values as strings. These metric types store their values in Prometheus as labels. For example, this is what a thermostat mode metric will look like from the exporter:

```
# HELP homekit_thermostat_livingroom_downstairs_mode Mode metric for device LivingRoom/Downstairs
# TYPE homekit_thermostat_livingroom_downstairs_mode gauge
homekit_thermostat_livingroom_downstairs_mode{mode="heat"} 1.0
```

Where the actual value is a meaningless "1", and the real data is, in this case mode="heat" (and as a thermostat, could also be "cool" or "off"). These lables are created and cleared automatically.

**NOTE**: This is sort of considered a poor use of Prometheus, so **use this at your own risk**.

Here is an example of a Grafana panel that uses a thermostat mode metric to show run mode in a State Timeline:

```
{
  "id": 6,
  "type": "state-timeline",
  "title": "",
  "gridPos": {
    "x": 0,
    "y": 8,
    "h": 2,
    "w": 12
  },
  "fieldConfig": {
    "defaults": {
      "custom": {
        "lineWidth": 0,
        "fillOpacity": 70,
        "spanNulls": 120000,
        "insertNulls": false,
        "hideFrom": {
          "tooltip": false,
          "viz": false,
          "legend": false
        },
        "axisPlacement": "auto"
      },
      "color": {
        "mode": "thresholds"
      },
      "mappings": [
        {
          "options": {
            "cool": {
              "color": "blue",
              "index": 2
            },
            "heat": {
              "color": "dark-red",
              "index": 0
            },
            "off": {
              "color": "#80808029",
              "index": 1
            }
          },
          "type": "value"
        }
      ],
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "green",
            "value": null
          }
        ]
      }
    },
    "overrides": [
      {
        "matcher": {
          "id": "byName",
          "options": "Metric"
        },
        "properties": [
          {
            "id": "displayName",
            "value": "Mode"
          }
        ]
      }
    ]
  },
  "transformations": [
    {
      "id": "seriesToRows",
      "options": {}
    },
    {
      "id": "organize",
      "options": {
        "excludeByName": {
          "Value": true
        },
        "includeByName": {},
        "indexByName": {},
        "renameByName": {}
      }
    }
  ],
  "pluginVersion": "12.4.0",
  "targets": [
    {
      "editorMode": "builder",
      "expr": "homekit_thermostat_masterbedroom_upstairs_mode",
      "legendFormat": "{{mode}}",
      "range": true,
      "refId": "A"
    }
  ],
  "datasource": {
    "type": "prometheus",
    "uid": "afeftskou718gf"
  },
  "options": {
    "mergeValues": true,
    "showValue": "never",
    "alignValue": "left",
    "rowHeight": 0.9,
    "legend": {
      "showLegend": false,
      "displayMode": "list",
      "placement": "bottom"
    },
    "tooltip": {
      "mode": "single",
      "sort": "none",
      "hideZeros": false
    }
  }
}
```
