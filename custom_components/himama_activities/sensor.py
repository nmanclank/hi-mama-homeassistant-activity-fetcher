"""Sensor platform for HiMama Activities."""
import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    child_id = entry.data["child_id"]
    
    async_add_entities([HiMamaActivitySensor(coordinator, child_id)])


class HiMamaActivitySensor(CoordinatorEntity):
    """Representation of a HiMama Activity Sensor."""

    def __init__(self, coordinator, child_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._child_id = child_id
        self._attr_name = f"HiMama Child {child_id} Latest Activity"
        self._attr_unique_id = f"himama_{child_id}_latest_activity"
        self._attr_icon = "mdi:child-toy"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data and len(self.coordinator.data) > 0:
            return self.coordinator.data[0].get("title", "Unknown")
        return "Unknown"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data:
            return {"activities": []}
            
        return {"activities": self.coordinator.data}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._child_id)},
            "name": f"HiMama Child {self._child_id}",
            "manufacturer": "HiMama",
            "model": "Activity Feed"
        }
