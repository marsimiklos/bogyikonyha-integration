import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
SCAN_INTERVAL = timedelta(hours=1)

# A Supervisor API proxy útvonala az Add-on API-jához
# Ez az útvonal a HA belső hálózaton keresztül érhető el hitelesítés nélkül,
# mivel a Core hívja a Supervisort.
ADDON_API_URL = "http://supervisor/addons/bogyikonya/api/pantry"

# --- Core Setup FÁZISOK (Helyes) ---

async def async_setup(hass: HomeAssistant, config: dict):
    """Az integráció betöltése."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integráció beállítása a konfigurációs bejegyzés alapján."""
    coordinator = BogyiKonyhaDataUpdateCoordinator(hass)
    
    # Első adatfrissítés végrehajtása
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integráció eltávolítása a config entry törlésekor."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


# --- Data Update Koordinátor (Javított API hívással) ---

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
        # HA aiohttp kliens használata
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self):
        """Adatok lekérése a Bogyi Konyha Add-on API-ról."""
        
        try:
            # Végrehajtjuk a GET kérést hitelesítő fejlécek nélkül,
            # bízva a Supervisor belső proxy működésében.
            async with self.session.get(ADDON_API_URL, timeout=10) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("API hiba (%s): %s - %s", response.status, ADDON_API_URL, error_text)
                    raise UpdateFailed(f"Add-on API hiba: {response.status}")

                data = await response.json()
                _LOGGER.debug("Sikeresen lekérdezett adatok: %s", data)
                return data
                
        except Exception as err:
            _LOGGER.error("Hiba az Add-on API lekérdezésekor: %s", err)
            raise UpdateFailed(f"Hiba az Add-on API lekérdezésekor: {err}")
