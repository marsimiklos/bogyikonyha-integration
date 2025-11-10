import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
# Ezen konstansok használata erősen ajánlott a szabványos HA viselkedéshez
from homeassistant.const import UnitOfVolume, UnitOfMass 
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# --- Segédfüggvény: Egység konverzió ---

def convert_unit_to_ha_const(unit_str: str) -> str | None:
    """A bejövő string egységet Home Assistant konstansra fordítja le."""
    if not unit_str:
        return None
        
    # Kisbetűsítjük az összehasonlításhoz
    normalized_unit = unit_str.lower().strip()
    
    # Tömeg egységek
    if normalized_unit in ["kg", "kilogramm"]:
        return UnitOfMass.KILOGRAMS
    if normalized_unit in ["g", "gramm"]:
        return UnitOfMass.GRAMS
    
    # Térfogat egységek
    if normalized_unit in ["l", "liter"]:
        return UnitOfVolume.LITERS
    if normalized_unit in ["ml", "milliliter"]:
        return UnitOfVolume.MILLILITERS
    
    # Db/Mennyiség (ezt általában None vagy egyedi string a HA-ban)
    if normalized_unit in ["db", "darab", "csomag"]:
        # "db" -t megtartjuk, ha az UnitOf... konstansok közül egyik sem illik
        return unit_str 
    
    return unit_str

# --- Setup Function ---

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Szenzorok beállítása a konfigurációs bejegyzéshez."""
    
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    
    # Két ellenőrzés a biztonságos inicializáláshoz:
    if not coordinator.data:
        _LOGGER.warning("Nincs lekérdezett adat a koordinátorban a szenzorok inicializálásához.")
        return
        
    if not isinstance(coordinator.data, list):
        _LOGGER.error("A kamra adat formátuma nem lista. Nem lehet szenzorokat létrehozni.")
        return

    # Minden egyes kamra elemhez létrehozunk egy szenzort
    for item in coordinator.data:
        # Csak azokat az elemeket vesszük, amelyeknek van "id" és "name" mezőjük
        if item.get('id') and item.get('name'):
             entities.append(PantryItemSensor(coordinator, item))
        else:
             _LOGGER.warning(f"Kamra elem kihagyva, hiányzó 'id' vagy 'name' mező: {item}")
             
    async_add_entities(entities)


# --- Sensor Entity Class ---

class PantryItemSensor(CoordinatorEntity, SensorEntity):
    """Egy adott kamra elem Home Assistant szenzora."""

    def __init__(self, coordinator, item_data):
        """Szenzor inicializálása. Az ID és a kezdeti név beállítása."""
        super().__init__(coordinator)
        
        # A kezdeti adatok mentése, amikből a Home Assistant entitás-ID-t képezzük
        self._id = item_data['id']
        self._name = item_data['name'].capitalize()
        
        # A Home Assistant szabványos property-jei
        self._attr_unique_id = f"{DOMAIN}_pantry_{self._id}"
        self._attr_name = f"Kamra: {self._name}"
        self._attr_icon = "mdi:food-apple" # Semleges ikon

    
    # --- Property-k a Home Assistant számára ---
    
    def _get_latest_item_data(self):
        """Segédfüggvény a legfrissebb kamra elem adatainak lekérésére."""
        if self.coordinator.data and isinstance(self.coordinator.data, list):
            return next((item for item in self.coordinator.data if item.get('id') == self._id), None)
        return None
        
    @property
    def native_value(self):
        """Az entitás aktuális állapota (mennyiség)."""
        latest_data = self._get_latest_item_data()
        if latest_data:
            return latest_data.get('quantity')
        return None # None beállítása, ha az adat hiányzik
        
    @property
    def native_unit_of_measurement(self):
        """A mérési egység (Home Assistant konstansra fordítva)."""
        latest_data = self._get_latest_item_data()
        if latest_data:
            unit_str = latest_data.get('unit')
            # Itt használjuk a konverziós segédfüggvényt
            return convert_unit_to_ha_const(unit_str)
        return None

    @property
    def extra_state_attributes(self):
        """További attribútumok (lejárati dátum, létrehozva, stb.)."""
        latest_data = self._get_latest_item_data()
        attributes = {}
        if latest_data:
            # Az összes kulcs/érték pár átemelése attribútumként
