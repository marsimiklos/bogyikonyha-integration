import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

# A hassio import szükséges a get_api() híváshoz és a HassioAPIError kivételhez
from homeassistant.components import hassio 
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
SCAN_INTERVAL = timedelta(hours=1) 

# --- Core Setup FÁZISOK ---

async def async_setup(hass: HomeAssistant, config: dict):
    """Az integráció betöltése a konfigurációs folyamat számára."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integráció beállítása a konfigurációs bejegyzés alapján."""
    coordinator = BogyiKonyhaDataUpdateCoordinator(hass)
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


# --- Data Update Koordinátor ---

class BogyiKonyhaDataUpdateCoordinator(DataUpdateCoordinator):
    """Az adatok frissítéséért felelős koordinátor. A Supervisor API Klienst használja."""

    def __init__(self, hass: HomeAssistant):
        """Inicializálás."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.addon_slug = "bogyikonya" 

    async def _async_update_data(self):
        """Adatok lekérése a Bogyi Konyha Add-on API-ról a Supervisor API-n keresztül."""
        
        try:
            # 1. Lekérjük a Supervisor API klienst: helyesen a hassio modulból hívva
            api = hassio.get_api(self.hass)
            
            # 2. Meghívjuk az Add-on API végpontot a kliensen keresztül
            response = await api.get(f"addons/{self.addon_slug}/api/pantry")

            return response

        except hassio.HassioAPIError as err:
            _LOGGER.error("Add-on API hiba a Supervisoron keresztül: %s", err)
            raise UpdateFailed(f"Add-on API hiba (Supervisor): {err}")
        except HomeAssistantError as err:
            _LOGGER.error("Hiba az Add-on API elérésében: %s", err)
            raise UpdateFailed(f"Hiba az Add-on API elérésében: {err}")
        except Exception as err:
            _LOGGER.error("Váratlan hiba az adatok frissítésekor: %s", err)
            raise UpdateFailed(f"Váratlan hiba: {err}")
