import logging

from homeassistant import config_entries
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

# A dominium neve (a mappa neve)
DOMAIN = "bogyikonya" 

class BogyiKonyhaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Bogyi Konyha Add-on konfigurációs folyamata."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Kezeli az első lépést, amikor a felhasználó hozzáadja az integrációt."""
        
        # 1. Ellenőrzés: Csak egy példányt engedélyezünk
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # 2. Megerősítés kérése
        if user_input is not None:
            # A felhasználó rákattintott a 'Küldés' gombra (vagy a 'Megerősítés'-re)
            # Mivel nincs szükség extra adatokra, azonnal létrehozzuk a bejegyzést
            return self.async_create_entry(title="Bogyi Konyha (Add-on)", data={})

        # 3. Információs űrlap megjelenítése
        # Egy űrlap, ami csak egy megerősítő gombot mutat (üres séma)
        return self.async_show_form(
            step_id="user",
            description_placeholders={"addon_slug": "bogyikonya"}
        )

    @callback
    def _async_get_existing_entry(self):
        """Ellenőrzi, hogy már létezik-e konfigurációs bejegyzés."""
        return self.hass.config_entries.async_entries(DOMAIN)
