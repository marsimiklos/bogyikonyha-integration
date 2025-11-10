import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
SCAN_INTERVAL = timedelta(hours=1)

# A Core integrációhoz NINCS szükség az ADDON_API_URL fixen definiálására,
# mert a címet a konfigurációból fogjuk kapni (ld. 3. pont: Config Flow)!

# --- Core Setup FÁZISOK ---

async def async_setup(hass: HomeAssistant, config: dict):
    """Az integráció betöltése."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integráció beállítása a konfigurációs bejegyzés alapján."""
    
    # Itt használjuk a konfigurációban megadott API címet:
    addon_api_url = entry.data.get("api_url") 
    if not addon_api_url:
        _LOGGER.error("Hiányzó API URL a konfigurációban.")
        return False

    coordinator = BogyiKonyhaDataUpdateCoordinator(hass, addon_api_url)
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    return True
# (async_unload_entry változatlan marad)
# ...

# --- Data Update Koordinátor (Csak a lényeges változások) ---

class BogyiKonyhaDataUpdateCoordinator(DataUpdateCoordinator):
    """Az adatok frissítéséért felelős koordinátor."""

    def __init__(self, hass: HomeAssistant, api_url: str):
        """Inicializálás."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.session = async_get_clientsession(hass)
        self.api_url = api_url # Az URL tárolása
        
    async def _async_update_data(self):
        """Adatok lekérése a Bogyi Konyha Add-on API-ról."""
        
        # Nincs szükség speciális fejlécekre, mert direkt hívás történik
        try:
            async with self.session.get(self.api_url, timeout=10) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("API hiba (%s): %s - %s", response.status, self.api_url, error_text)
                    raise UpdateFailed(f"Add-on API hiba: {response.status}")

                data = await response.json()
                return data
                
        except Exception as err:
            _LOGGER.error("Hiba az Add-on API lekérdezésekor: %s", err)
            raise UpdateFailed(f"Hiba az Add-on API lekérdezésekor: {err}")
