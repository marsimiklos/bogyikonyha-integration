import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfVolume, UnitOfMass # Használd a konstansokat

from . import DOMAIN # Az __init__.py-ban definiált DOMAIN importálása

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Szenzorok beállítása a konfigurációs bejegyzéshez."""
    
    # A koordinátor lekérése az __init__.py-ból
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Minden egyes kamra elemhez létrehozunk egy szenzort
    for item in coordinator.data:
        entities.append(PantryItemSensor(coordinator, item))
        
    async_add_entities(entities)


class PantryItemSensor(CoordinatorEntity, SensorEntity):
    """Egy adott kamra elem Home Assistant szenzora."""

    def __init__(self, coordinator, item_data):
        """Szenzor inicializálása."""
        super().__init__(coordinator)
        self._item_data = item_data
        self._id = item_data['id']
        self._name = item_data['name'].capitalize()
        
    @property
    def unique_id(self) -> str:
        """Egyedi azonosító a Home Assistant számára."""
        return f"{DOMAIN}_pantry_{self._id}"

    @property
    def name(self) -> str:
        """Az entitás neve."""
        return f"Kamra {self._name}"

    @property
    def state(self):
        """Az entitás aktuális állapota (mennyiség)."""
        # Lekérjük a legfrissebb adatot a koordinátorból
        latest_data = next((item for item in self.coordinator.data if item['id'] == self._id), None)
        if latest_data:
            return latest_data.get('quantity')
        return None

    @property
    def unit_of_measurement(self):
        """A mérési egység."""
        latest_data = next((item for item in self.coordinator.data if item['id'] == self._id), None)
        if latest_data and latest_data.get('unit'):
            # Itt lehetne egység-konverziót végezni, de most csak a stringet adjuk vissza
            return latest_data['unit']
        return None

    @property
    def extra_state_attributes(self):
        """További attribútumok (lejárati dátum, létrehozva)."""
        latest_data = next((item for item in self.coordinator.data if item['id'] == self._id), None)
        if latest_data:
            return {
                "item_id": self._id,
                "expiry_date": latest_data.get('expiryDate'),
                "created_at": latest_data.get('createdAt'),
            }
        return {}

    @property
    def icon(self):
        """Ikon a dashboardhoz."""
        # Itt lehetne logikát beépíteni a lejárati dátum alapján
        return "mdi:food-drumstick"
