import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.components import hassio # FONTOS: Hassio importálása

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
ADDON_SLUG = "bogyikonya" # Az Add-on azonosítója a manifest.json szerint

class BogyiKonyhaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Bogyi Konyha Add-on konfigurációs folyamata."""
    
    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Kezeli a konfiguráció első lépését, ami AUTOMATIKUSAN KINYERI az URL-t."""
        
        # 1. Csak egy példányt engedélyezünk
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # 2. Ellenőrzés: Csak HA OS/Supervised alatt működik
        if not hassio.is_hassio(self.hass):
            return self.async_abort(reason="not_hassio")

        try:
            # 3. Lekérdezzük az Add-on részletes adatait
            addon_info = await hassio.async_get_addon_info(self.hass, ADDON_SLUG)
            
            if not addon_info:
                return self.async_abort(reason="addon_not_found")
            
            if addon_info["state"] != "started":
                 return self.async_abort(reason="addon_not_running")
            
            # 4. Összeállítjuk az Add-on belső hálózati címét
            # Használjuk a Supervisor által biztosított IP-t és a 8099-es portot
            addon_ip = addon_info["host"] 
            addon_api_url = f"http://{addon_ip}:8099/api/pantry"

        except Exception as err:
            _LOGGER.error("Hiba az Add-on infó lekérésekor: %s", err)
            return self.async_abort(reason="addon_info_failed")
            
        # 5. Sikeresen kinyertük az API címet, most létrehozzuk a bejegyzést
        return self.async_create_entry(
            title="Bogyi Konyha (Add-on)",
            # Átadjuk az URL-t a __init__.py-nak a 'data' szótárban
            data={"api_url": addon_api_url} 
        )
