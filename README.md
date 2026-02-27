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

Prometheus can only store numeric data. Any device state reporting a string (e.g. Garage door that has a state of "open" or "closed") will currently be ignored.
