import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
SCAN_INTERVAL = timedelta(hours=1) # Frissítés óránként

# A Home Assistant Core API proxy útvonala az Add-onod API-jához
# Belső hívás, HTTP és a 'supervisor' hoszt elegendő.
ADDON_API_URL = "http://supervisor/addons/bogyikonya/api/pantry"


async def async_setup(hass: HomeAssistant, config: dict):
    """Az integráció betöltése a konfigurációs folyamat számára."""
    # Mivel config_flow-t használunk, ez a funkció csak annyit tesz, 
    # hogy jelzi a HA-nak, hogy az integráció sikeresen betöltött.
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry):
    """Integráció beállítása a konfigurációs bejegyzés alapján."""
    
    # 1. Koordinátor beállítása a Home Assistant Core-ban
    coordinator = BogyiKonyhaDataUpdateCoordinator(hass)
    
    # 2. Első adatfrissítés elvégzése (blokkolás nélkül)
    await coordinator.async_config_entry_first_refresh()

    # 3. Adat tárolása a hass.data szótárban
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 4. Szenzor entitások beállítása (sensor.py-ra utal)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    
    return True

class BogyiKonyhaDataUpdateCoordinator(DataUpdateCoordinator):
    """Az adatok frissítéséért felelős koordinátor."""

    def __init__(self, hass: HomeAssistant):
        """Inicializálás."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        # HASSIO környezetben a Home Assistant aiohttp kliensét használjuk
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self):
        """Adatok lekérése a Bogyi Konyha Add-on API-ról."""
        try:
            # 1. Lekérdezés a Home Assistant Core-on keresztül
            async with self.session.get(ADDON_API_URL) as response:
                
                # 2. Hibakezelés
                if response.status != 200:
                    error_text = await response.text()
                    raise UpdateFailed(f"API hiba: {response.status} - {error_text}")

                # 3. JSON adatok visszaadása (Kamra elemek listája)
                data = await response.json()
                return data
                
        except Exception as err:
            raise UpdateFailed(f"Hiba az Add-on API lekérdezésekor: {err}")
