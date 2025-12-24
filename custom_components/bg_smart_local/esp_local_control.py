"""ESP Local Control Protocol Handler."""
import asyncio
import json
import logging
from typing import Optional, Dict, Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# For now, use a stub implementation until protobuf is set up
# Replace this with actual protobuf import once generated


class ESPLocalDevice:
    """ESP Local Control Device."""
    
    def __init__(self, host: str, port: int, node_id: str, pop: str, security_type: int):
        """Initialize device."""
        self.host = host
        self.port = port
        self.node_id = node_id
        self.pop = pop
        self.security_type = security_type
        self.base_url = f"http://{host}:{port}"
        self.control_path = "esp_local_ctrl/control"
        self.property_count = -1
        self._params_cache = {}
        
        _LOGGER.info(
            "Initialized ESPLocalDevice: host=%s, port=%s, security=%s",
            host, port, security_type
        )
    
    async def _send_raw_request(self, data: bytes) -> Optional[bytes]:
        """Send raw HTTP request."""
        url = f"{self.base_url}/{self.control_path}"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
            "Connection": "Keep-Alive"
        }
        
        _LOGGER.debug("Sending request to %s (payload size: %d bytes)", url, len(data))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    data=data, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        body = await response.read()
                        _LOGGER.debug("Received response: %d bytes", len(body))
                        return body
                    else:
                        _LOGGER.error("HTTP error: %s", response.status)
                        return None
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error: %s", e)
            return None
        except Exception as e:
            _LOGGER.error("Unexpected error: %s", e, exc_info=True)
            return None
    
    async def get_property_count(self) -> int:
        """Get the number of properties."""
        if self.property_count > 0:
            _LOGGER.debug("Using cached property count: %d", self.property_count)
            return self.property_count
        
        _LOGGER.debug("Getting property count from device")
        
        # For testing: return 2 (standard for ESP local control)
        # TODO: Replace with actual protobuf call
        _LOGGER.warning("Using stub implementation - returning property count = 2")
        self.property_count = 2
        return 2
    
    async def get_property_values(self) -> Optional[Dict[str, Any]]:
        """Get all property values."""
        _LOGGER.debug("Getting property values")
        
        count = await self.get_property_count()
        if count <= 0:
            _LOGGER.error("Invalid property count: %d", count)
            return None
        
        # TODO: Replace with actual protobuf implementation
        # For now, return stub data for testing
        _LOGGER.warning("Using stub implementation for get_property_values")
        
        stub_properties = {
            "config": {
                "node_id": self.node_id or "test_node",
                "firmware": "1.0.0"
            },
            "params": {
                "Switch": {
                    "Power": {"power": 0},
                    "Brightness": {"brightness": 0}
                }
            }
        }
        
        _LOGGER.info("Properties: %s", stub_properties)
        
        # Cache params
        if "params" in stub_properties:
            self._params_cache = stub_properties["params"]
        
        return stub_properties
    
    async def set_property_values(self, params_json: Dict[str, Any]) -> bool:
        """Set device parameters."""
        _LOGGER.debug("Setting property values: %s", params_json)
        
        # TODO: Replace with actual protobuf implementation
        _LOGGER.warning("Using stub implementation for set_property_values")
        
        # Update cache
        for key, value in params_json.items():
            if key in self._params_cache:
                if isinstance(self._params_cache[key], dict) and isinstance(value, dict):
                    self._params_cache[key].update(value)
                else:
                    self._params_cache[key] = value
        
        _LOGGER.info("Set properties successful (stub)")
        return True
    
    async def get_params(self) -> Dict[str, Any]:
        """Get current device params."""
        _LOGGER.debug("Getting params")
        
        if not self._params_cache:
            properties = await self.get_property_values()
            if properties and "params" in properties:
                self._params_cache = properties["params"]
                _LOGGER.debug("Cached params: %s", self._params_cache)
        
        return self._params_cache
    
    async def set_param(self, device_name: str, param_name: str, value: Any) -> bool:
        """Set a specific parameter."""
        _LOGGER.debug(
            "Setting param: device=%s, param=%s, value=%s",
            device_name, param_name, value
        )
        
        params = {
            device_name: {
                param_name: value
            }
        }
        
        return await self.set_property_values(params)