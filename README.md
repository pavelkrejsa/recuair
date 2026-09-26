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

It also provides control entities:

- **Light**: Native Home Assistant light entity (`light.xxx`) with on/off, brightness and RGB color control
- **Mode (Select)**: `auto`, `off`, `holiday`, `bypass`, `1`, `2`, `3`, `4`
- **Light Intensity (Number)**: 0-5

## Install with HACS

1. In Home Assistant, open **HACS** and choose **Integrations**.
2. Open the HACS menu, select **Custom repositories**, and add `https://github.com/pavelkrejsa/recuair` with category **Integration**.
3. Find **Recuair** in HACS and download it.
4. Restart Home Assistant to load the integration.
5. Go to **Settings** > **Devices & Services**, select **Add Integration**, and search for **Recuair**.

After installation, the DC40 should appear automatically in Home Assistant's discovered integrations. If it does not, add Recuair manually and enter its IP address.

## Configuration

During the setup process, you will be prompted to enter the following information:

- **Host**: The local IP address of your Recuair ventilation unit (e.g., `192.168.1.123`).
- **Scan Interval** Periodical check interval for new data, default is 60s.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
