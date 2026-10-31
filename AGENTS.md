# Recuair Home Assistant integration

This is a Home Assistant custom component for Recuair DC40 ventilation units. It allows you to monitor your Recuair unit's status directly from Home Assistant.

## Features

- Reads sensor data from the local web interface of the Recuair unit.
- Creates the following sensors in Home Assistant:
  - CO2 Level (ppm)
  - Room Temperature (°C)
  - Outside Temperature (°C)
  - Humidity (%)
  - Ventilation Intensity (%)
  - Filter Status (%)
  - Current Mode (e.g., AUTO)
  - Light Intensity (0-5)
- Displays the Recuair logo for the integration in Home Assistant.

## Technology Used

- **Python** with `aiohttp` for asynchronous web requests.
- **BeautifulSoup** for HTML parsing and data scraping.
- The integration connects to the local IP address of the Recuair unit, as no official API is available.

## Setup

1. Copy the `custom_components/recuair` directory to your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Add the "Recuair" integration via the "Devices & Services" page, providing the IP address of your unit.
