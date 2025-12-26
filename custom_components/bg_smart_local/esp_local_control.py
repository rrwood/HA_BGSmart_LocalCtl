"""ESP Local Control Protocol Handler - Final Implementation..."""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List

import aiohttp

# Import the generated protobuf messages
try:
    from . import esp_local_ctrl_pb2 as pb
    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False
    import warnings
    warnings.warn("Protobuf messages not available. Run: python -m grpc_tools.protoc -I. --python_out=. esp_local_ctrl.proto")

_LOGGER = logging.getLogger(__name__)


class ESPLocalDevice:
    """ESP Local Control Device - Final Implementation."""
    
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
        
        if not PROTOBUF_AVAILABLE:
            _LOGGER.error("Protobuf messages not available! Integration will not work.")
        
        _LOGGER.info(
            "Initialized ESPLocalDevice: host=%s, port=%s, security=%s, protobuf=%s",
            host, port, security_type, PROTOBUF_AVAILABLE
        )
    
    async def _send_protobuf_request(self, message) -> Optional[bytes]:
        """Send protobuf request and get response."""
        if not PROTOBUF_AVAILABLE:
            _LOGGER.error("Cannot send request: protobuf not available")
            return None
        
        url = f"{self.base_url}/{self.control_path}"
        payload = message.SerializeToString()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
            "Connection": "Keep-Alive"
        }
        
        _LOGGER.debug("Sending protobuf request to %s (payload: %d bytes)", url, len(payload))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    data=payload, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        body = await response.read()
                        _LOGGER.debug("Received response: %d bytes", len(body))
                        return body
                    else:
                        _LOGGER.error("HTTP error: %s", response.status)
                        text = await response.text()
                        _LOGGER.error("Response body: %s", text)
                        return None
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error: %s", e)
            return None
        except Exception as e:
            _LOGGER.error("Unexpected error: %s", e, exc_info=True)
            return None
    
    async def get_property_count(self) -> int:
        """Get the number of properties from device."""
        if not PROTOBUF_AVAILABLE:
            _LOGGER.error("Protobuf not available")
            return -1
        
        if self.property_count > 0:
            _LOGGER.debug("Using cached property count: %d", self.property_count)
            return self.property_count
        
        _LOGGER.debug("Getting property count from device")
        
        request = pb.LocalCtrlMessage(
            msg=pb.TypeCmdGetPropertyCount,
            cmd_get_prop_count=pb.CmdGetPropertyCount()
        )
        
        response_data = await self._send_protobuf_request(request)
        if not response_data:
            _LOGGER.error("Failed to get property count")
            return -1
        
        try:
            response = pb.LocalCtrlMessage()
            response.ParseFromString(response_data)
            
            if response.HasField('resp_get_prop_count'):
                status = response.resp_get_prop_count.status
                if status == pb.Success:
                    self.property_count = response.resp_get_prop_count.count
                    _LOGGER.info("Property count: %d", self.property_count)
                    return self.property_count
                else:
                    _LOGGER.error("Get property count failed with status: %s", status)
            else:
                _LOGGER.error("Response does not contain resp_get_prop_count")
        except Exception as e:
            _LOGGER.error("Failed to parse response: %s", e, exc_info=True)
        
        return -1
    
    async def get_property_values(self) -> Optional[Dict[str, Any]]:
        """Get all property values from device."""
        if not PROTOBUF_AVAILABLE:
            _LOGGER.error("Protobuf not available")
            return None
        
        _LOGGER.debug("Getting property values")
        
        count = await self.get_property_count()
        if count <= 0:
            _LOGGER.error("Invalid property count: %d", count)
            return None
        
        request = pb.LocalCtrlMessage(
            msg=pb.TypeCmdGetPropertyValues,
            cmd_get_prop_vals=pb.CmdGetPropertyValues(
                indices=list(range(count))
            )
        )
        
        response_data = await self._send_protobuf_request(request)
        if not response_data:
            _LOGGER.error("Failed to get property values")
            return None
        
        try:
            response = pb.LocalCtrlMessage()
            response.ParseFromString(response_data)
            
            if not response.HasField('resp_get_prop_vals'):
                _LOGGER.error("Response does not contain resp_get_prop_vals")
                return None
            
            if response.resp_get_prop_vals.status != pb.Success:
                _LOGGER.error("Get property values failed with status: %s", 
                            response.resp_get_prop_vals.status)
                return None
            
            properties = {}
            for prop_info in response.resp_get_prop_vals.props:
                try:
                    prop_name = prop_info.name
                    prop_value_bytes = prop_info.value
                    prop_value_str = prop_value_bytes.decode('utf-8')
                    prop_value = json.loads(prop_value_str)
                    
                    properties[prop_name] = prop_value
                    _LOGGER.debug("Property '%s': %s", prop_name, prop_value)
                    
                    if prop_name == "params":
                        self._params_cache = prop_value
                        
                except Exception as e:
                    _LOGGER.error("Failed to parse property %s: %s", prop_info.name, e)
            
            _LOGGER.info("Retrieved %d properties from device", len(properties))
            return properties
            
        except Exception as e:
            _LOGGER.error("Failed to parse response: %s", e, exc_info=True)
            return None
    
    async def set_property_values(self, params_json: Dict[str, Any]) -> bool:
        """Set device parameters."""
        if not PROTOBUF_AVAILABLE:
            _LOGGER.error("Protobuf not available")
            return False
        
        _LOGGER.debug("Setting property values: %s", params_json)
        
        json_str = json.dumps(params_json)
        json_bytes = json_str.encode('utf-8')
        
        request = pb.LocalCtrlMessage(
            msg=pb.TypeCmdSetPropertyValues,
            cmd_set_prop_vals=pb.CmdSetPropertyValues(
                props=[
                    pb.PropertyValue(
                        index=1,  # Index 1 is "params"
                        value=json_bytes
                    )
                ]
            )
        )
        
        response_data = await self._send_protobuf_request(request)
        if not response_data:
            _LOGGER.error("Failed to set property values")
            return False
        
        try:
            response = pb.LocalCtrlMessage()
            response.ParseFromString(response_data)
            
            if not response.HasField('resp_set_prop_vals'):
                _LOGGER.error("Response does not contain resp_set_prop_vals")
                return False
            
            if response.resp_set_prop_vals.status == pb.Success:
                _LOGGER.info("Set property values successful")
                
                # Update cache with the new values
                for device_name, params in params_json.items():
                    if device_name not in self._params_cache:
                        self._params_cache[device_name] = {}
                    
                    # Merge the updates into cache
                    for param_name, param_value in params.items():
                        self._params_cache[device_name][param_name] = param_value
                
                return True
            else:
                _LOGGER.error("Set property values failed with status: %s",
                            response.resp_set_prop_vals.status)
                return False
                
        except Exception as e:
            _LOGGER.error("Failed to parse response: %s", e, exc_info=True)
            return False
    
    async def get_params(self) -> Dict[str, Any]:
        """Get current device params."""
        _LOGGER.debug("Getting params")
        
        if not self._params_cache:
            properties = await self.get_property_values()
            if properties and "params" in properties:
                self._params_cache = properties["params"]
                _LOGGER.debug("Cached params: %s", self._params_cache)
            else:
                _LOGGER.warning("No params found in properties")
        
        return self._params_cache
    
    async def set_param(self, device_name: str, param_name: str, value: Any) -> bool:
        """Set a specific parameter.
        
        The device expects the full nested structure:
        {
            "DMHCM": {
                "Power": true,
                "brightness": 75
            }
        }
        
        Note: Values are sent directly (bool, int, string), not wrapped in dicts.
        """
        _LOGGER.debug(
            "Setting param: device=%s, param=%s, value=%s (type=%s)",
            device_name, param_name, value, type(value).__name__
        )
        
        # Build the params structure with the direct value
        params = {
            device_name: {
                param_name: value
            }
        }
        
        return await self.set_property_values(params)