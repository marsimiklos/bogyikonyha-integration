import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

# Szükséges importok a Supervisor API híváshoz
from homeassistant.components import hassio 
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
SCAN_INTERVAL = timedelta(hours=1) # Frissítés óránként

async def async_setup(hass: HomeAssistant, config: dict):
    """Az integráció betöltése a konfigurációs folyamat számára."""
    # Mivel config_flow-t használunk, ez a funkció csak annyit tesz,  
    # hogy jelzi a HA-nak, hogy az integráció sikeresen betöltött.
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integráció beállítása a konfigurációs bejegyzés alapján."""
    
    # 1. Koordinátor beállítása a Home Assistant Core-ban
    coordinator = BogyiKonyhaDataUpdateCoordinator(hass)
    
    # 2. Első adatfrissítés elvégzése (blokkolás nélkül)
    await coordinator.async_config_entry_first_refresh()

    # 3. Adat tárolása a hass.data szótárban
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 4. Szenzor entitások beállítása (sensor.py-ra utal)
    # A hass.async_create_task elavult lehet a modern HA-ban, 
    # helyette a közvetlen hívás ajánlott:
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    
    return True

# Opcionális: a config entry eltávolításának kezelése
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integráció eltávolítása a config entry törlésekor."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class BogyiKonyhaDataUpdateCoordinator(DataUpdateCoordinator):
    """Az adatok frissítéséért felelős koordinátor. A Supervisor API-t használja."""

    def __init__(self, hass: HomeAssistant):
        """Inicializálás."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        # Az Add-on slug (ID) tárolása
        self.addon_slug = "bogyikonya" 

    async def _async_update_data(self):
        """Adatok lekérése a Bogyi Konyha Add-on API-ról a Supervisor API-n keresztül."""
        
        # A VÁLTOZÁS ITT VAN: HITETESÍTETT HÍVÁS A SUPERVISOR-ON KERESZTÜL
        try:
            # A hassio.async_send_command automatikusan kezeli a tokent és a hitelesítést.
            
            # API ÚTVONAL: /addons/{slug}/api/pantry
            # MÓDSZER: GET
            data = await hassio.async_send_command(
                self.hass,
                "addons/{slug}/api/pantry".format(slug=self.addon_slug),
                "get", 
                None # A GET kéréshez nincs szükség body-ra
            )

            # A hassio.async_send_command a válasz tartalmát (JSON-t) adja vissza, 
            # vagy HomeAssistantError-t/HassioAPIError-t dob hiba esetén.
            return data

        except hassio.HassioAPIError as err:
            # Add-on specifikus hiba (pl. 404, 500 az Add-on API-ján)
            _LOGGER.error("Add-on API hiba a Supervisoron keresztül: %s", err)
            raise UpdateFailed(f"Add-on API hiba (Supervisor): {err}")
        except HomeAssistantError as err:
            # Home Assistant Core hiba (pl. rossz slug, timeout)
            _LOGGER.error("Hiba az Add-on API elérésében: %s", err)
            raise UpdateFailed(f"Hiba az Add-on API elérésében: {err}")
        except Exception as err:
            _LOGGER.error("Váratlan hiba az adatok frissítésekor: %s", err)
            raise UpdateFailed(f"Váratlan hiba: {err}")
