import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.components import hassio # Továbbra is szükség van rá a környezet ellenőrzéséhez

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bogyikonya"
ADDON_SLUG = "bogyikonya" # Az Add-on azonosítója a manifest.json szerint

class BogyiKonyhaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Bogyi Konyha Add-on konfigurációs folyamata."""
    
    VERSION = 3 # Verziószám növelése a változás jelzésére
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Kezeli a konfiguráció első lépését, ami AUTOMATIKUSAN KINYERI az URL-t."""
        
        # 1. Ellenőrzés: Csak egy példányt engedélyezünk
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # 2. Ellenőrzés: Csak HA OS/Supervised alatt működik
        if not hassio.is_hassio(self.hass):
            return self.async_abort(reason="not_hassio")

        # ÚJ: Supervisor API kliens beszerzése
        try:
            supervisor_client = hassio.get_api_client(self.hass)
        except Exception:
            # Ha valamiért nem sikerül a kliens beszerzése (ritka)
            return self.async_abort(reason="supervisor_api_unavailable")

        # 3. Lekérdezzük az Add-on részletes adatait a kliensen keresztül
        try:
            # A kliens GET metódusával lekérjük az /addons/{slug}/info végpontot
            addon_info = await supervisor_client.get(f"addons/{ADDON_SLUG}/info")
            
            if not addon_info or not addon_info.get('data'):
                return self.async_abort(reason="addon_not_found")
            
            addon_data = addon_info['data']

            if addon_data.get("state") != "started":
                 return self.async_abort(reason="addon_not_running")
            
            # 4. Összeállítjuk az Add-on belső hálózati címét
            # Az IP a 'host' mezőben található
            addon_ip = addon_data["host"] 
            
            # A webszerver portja az app.py-ban: 8099
            addon_api_url = f"http://{addon_ip}:8099/api/pantry"

        except Exception as err:
            _LOGGER.error("Hiba az Add-on infó lekérésekor a Supervisor kliensen keresztül: %s", err)
            return self.async_abort(reason="addon_info_failed")
            
        # 5. Sikeresen kinyertük az API címet, most létrehozzuk a bejegyzést
        return self.async_create_entry(
            title="Bogyi Konyha (Add-on)",
            # Átadjuk az URL-t a __init__.py-nak a 'data' szótárban
            data={"api_url": addon_api_url} 
        )
