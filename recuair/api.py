"""API for Recuair."""
import logging
import aiohttp
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

class RecuairApi:
    """Recuair API."""

    def __init__(self, ip_address: str, session: aiohttp.ClientSession):
        """Initialize the API."""
        self._ip_address = ip_address
        self._url = f"http://{self._ip_address}/"
        self._session = session

    async def get_data(self):
        """Get data from the Recuair unit."""
        try:
            async with self._session.get(self._url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                return self._parse_data(soup)
        except Exception as e:
            _LOGGER.error("Error fetching data from Recuair unit: %s", e)
            return None

    def _parse_data(self, soup):
        """Parse data from the HTML."""
        data = {}

        # Device Name
        device_name_span = soup.find("span", class_="deviceName")
        if device_name_span:
            data["device_name"] = device_name_span.text.strip()

        # Temperatures and Humidity
        temp_span = soup.find("span", class_="bigText")
        if temp_span:
            text = temp_span.text.strip()
            parts = text.split("/")
            if len(parts) == 2:
                # "25 °C / 45 % "
                room_temp_str = parts[0]
                humidity_str = parts[1].split("%")[0]
                try:
                    data["room_temperature"] = int(room_temp_str.replace("°C", "").strip())
                    data["humidity"] = int(humidity_str.strip())
                except ValueError:
                    pass # Could not parse

            # There is a second part of the span for outside temp
            outside_temp_i = temp_span.find("i", class_="logo_termo_2")
            if outside_temp_i:
                outside_temp_text = outside_temp_i.next_sibling
                if outside_temp_text:
                    try:
                        data["outside_temperature"] = int(outside_temp_text.replace("°C", "").strip())
                    except (ValueError, AttributeError):
                        pass # Could not parse

        # Mode
        button = soup.find("button", onclick="showModal('regimeModal')")
        if button and button.parent and button.parent.parent:
            mode_div = button.parent.parent.find_next("div")
            if mode_div:
                mode_span = mode_div.find("span", class_="bigText")
                if mode_span:
                    data["mode"] = mode_span.text.strip()


        # CO2
        co2_b = soup.find("b", string=lambda t: t and "ppm" in t)
        if co2_b:
            try:
                data["co2"] = int(co2_b.text.replace("ppm", "").strip())
            except ValueError:
                pass # Could not parse

        # Filter Status
        button = soup.find("button", onclick="showModal('filterModal')")
        if button and button.parent and button.parent.parent:
            filter_box = button.parent.parent.find_next_sibling("div", class_="filterBox")
            if filter_box:
                filter_div = filter_box.find("div")
                if filter_div and filter_div.has_attr("style"):
                    style = filter_div["style"] # "width: 60%"
                    try:
                        value = int(style.split(":")[1].replace("%", "").strip())
                        data["filter_status"] = 100 - value
                    except (ValueError, IndexError):
                        pass

        # Ventilation Intensity
        vent_header = soup.find("span", string=lambda t: t and "Ventilation intensity" in t)
        if vent_header:
            vent_box = vent_header.find_next("div", class_="bigText coText")
            if vent_box:
                vent_div = vent_box.find("div", class_="filterBox")
                if vent_div:
                    width_div = vent_div.find("div")
                    if width_div and width_div.has_attr("style"):
                        style = width_div["style"] # "width: 75%;"
                        try:
                            value = int(style.split(":")[1].replace("%;", "").replace("%", "").strip())
                            data["ventilation_intensity"] = 100 - value
                        except (ValueError, IndexError):
                            pass

        # Light Intensity
        intensity_input = soup.find("input", {"name": "intensity"})
        if intensity_input and intensity_input.has_attr("value"):
            try:
                data["light_intensity"] = int(intensity_input["value"])
            except (ValueError, TypeError):
                pass

        # Firmware Version
        fw_div = soup.find("div", string=lambda t: t and "fw:" in t)
        if fw_div:
            text = fw_div.text.strip()
            parts = text.split()
            for part in parts:
                if "fw:" in part:
                    fw_version = part.replace("fw:", "")
                    data["firmware_version"] = fw_version
                    break
        return data