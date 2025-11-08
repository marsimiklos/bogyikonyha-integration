import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

# A hassio import szükséges az elérhetőség ellenőrzéséhez és a get_api() híváshoz
from homeassistant.components import hassio 
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
SCAN_INTERVAL = timedelta(hours=1) # Frissítés óránként

# --- Core Setup FÁZISOK ---

async def async_setup(hass: HomeAssistant, config: dict):
    """Az integráció betöltése a konfigurációs folyamat számára."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integráció beállítása a konfigurációs bejegyzés alapján."""
    
    # 1. Koordinátor beállítása
    coordinator = BogyiKonyhaDataUpdateCoordinator(hass)
    
    # 2. Első adatfrissítés (blokkolás nélkül)
    await coordinator.async_config_entry_first_refresh()

    # 3. Adat tárolása
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 4. Szenzor entitások beállítása (forward a sensor.py-ra)
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
        
        # 1. Supervisor elérhetőségének ellenőrzése
        if not hassio.is_loaded(self.hass):
            _LOGGER.error("A Supervisor szolgáltatás nem elérhető. Az Add-on API hívás sikertelen.")
            raise UpdateFailed("A Supervisor szolgáltatás nem elérhető.")

        try:
            # 2. Lekérjük a Supervisor API klienst, ami kezeli a tokent
            # A get_api() metódus a helyes útvonal a kliens eléréséhez.
            api = self.hass.components.hassio.get_api()
            
            # 3. Meghívjuk az Add-on API végpontot a kliensen keresztül
            # Az Add-on API elérésének útvonala a Supervisor számára: /addons/{slug}/api/{végpont}
            # Az api.get() metódus automatikusan POST/GET kéréseket indít a Supervisor felé.
            response = await api.get(f"addons/{self.addon_slug}/api/pantry")

            # Ha a hívás sikeres, a response már a JSON tartalom.
            return response

        except hassio.HassioAPIError as err:
            # Add-on specifikus hiba
            _LOGGER.error("Add-on API hiba a Supervisoron keresztül: %s", err)
            raise UpdateFailed(f"Add-on API hiba (Supervisor): {err}")
        except HomeAssistantError as err:
            # Home Assistant Core hiba
            _LOGGER.error("Hiba az Add-on API elérésében: %s", err)
            raise UpdateFailed(f"Hiba az Add-on API elérésében: {err}")
        except Exception as err:
            _LOGGER.error("Váratlan hiba az adatok frissítésekor: %s", err)
            raise UpdateFailed(f"Váratlan hiba: {err}")
