# Recuair Home Assistant Integration

This is a custom component for [Home Assistant](https://www.home-assistant.io/) to integrate with [Recuair DC40](https://www.recuair.com/) ventilation units. It allows you to monitor your Recuair unit's status directly from Home Assistant by reading data from its local web interface.

## How it Works

This integration scrapes the local web interface of the Recuair unit, as no official API is available. It uses `aiohttp` for asynchronous web requests and `BeautifulSoup` for HTML parsing to extract sensor data.

## Features

Once configured, the integration will create the following sensors in Home Assistant:

- **CO2 Level**: Current CO2 concentration (ppm)
- **Room Temperature**: Indoor temperature (°C)
- **Outside Temperature**: Outdoor temperature (°C)
- **Humidity**: Indoor humidity (%)
- **Ventilation Intensity**: Current fan speed (%)
- **Filter Status**: Remaining filter life (%)
- **Mode**: Current operating mode (e.g., AUTO, MANUAL)
- **Light Intensity**: On-device light intensity level (0-5)

## Setup

1. **Copy Files**: Copy the `recuair` directory into your Home Assistant `custom_components` folder.
2. **Restart Home Assistant**: Restart your Home Assistant instance to allow it to detect the new integration.
3. **Add Integration**:
    - Navigate to **Settings** > **Devices & Services**.
    - Click the **+ ADD INTEGRATION** button.
    - Search for "Recuair" and select it.

## Configuration

During the setup process, you will be prompted to enter the following information:

- **Host**: The local IP address of your Recuair ventilation unit (e.g., `192.168.1.123`).
- **Scan Interval** Periodical check interval for new data, default is 60s.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
