"""ESP Local Control - Simple stub for testing."""
import logging

_LOGGER = logging.getLogger(__name__)


class ESPLocalDevice:
    """ESP Local Control Device - Test stub."""
    
    def __init__(self, host: str, port: int, node_id: str, pop: str, security_type: int):
        """Initialize the device."""
        self.host = host
        self.port = port
        self.node_id = node_id
        self.pop = pop
        self.security_type = security_type
        _LOGGER.info("Initialized device at %s:%s", host, port)
    
    async def get_property_count(self) -> int:
        """Get property count - stub returns 2."""
        _LOGGER.info("Getting property count (stub)")
        return 2
    
    async def get_params(self) -> dict:
        """Get device params - stub."""
        _LOGGER.info("Getting params (stub)")
        return {
            "Switch 1": {
                "Power": {"power": 0},
                "Brightness": {"brightness": 0}
            }
        }
    
    async def set_param(self, device_name: str, param_name: str, value: dict) -> bool:
        """Set parameter - stub."""
        _LOGGER.info("Setting param %s.%s = %s (stub)", device_name, param_name, value)
        return True
