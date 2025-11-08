import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession # Újra kell!

# A hassio importot már nem használjuk, hogy elkerüljük a get_api hibát

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
SCAN_INTERVAL = timedelta(hours=1) 

# A supervisor API URL-t visszaállítjuk
ADDON_API_URL = "http://supervisor/addons/bogyikonya/api/pantry"

# --- Core Setup FÁZISOK (Változatlan) ---

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


# --- Data Update Koordinátor (Token manuális hozzáadásával) ---

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
        # Session beállítása
        self.session = async_get_clientsession(hass)
        self.addon_slug = "bogyikonya" 

    async def _async_update_data(self):
        """Adatok lekérése a Bogyi Konyha Add-on API-ról."""
        
        try:
            # 1. Lekérjük a Home Assistant Core access tokent
            access_token = self.hass.auth.async_get_access_token()
            
            # 2. Összeállítjuk a hitelesítő fejlécet
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            # 3. Végrehajtjuk a hitelesített GET kérést
            async with self.session.get(ADDON_API_URL, headers=headers) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise UpdateFailed(f"API hiba: {response.status} - {error_text}")

                data = await response.json()
                return data
                
        except Exception as err:
            _LOGGER.error("Hiba az Add-on API lekérdezésekor: %s", err)
            raise UpdateFailed(f"Hiba az Add-on API lekérdezésekor: {err}")
