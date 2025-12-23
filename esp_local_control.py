# esp_local_control.py
import asyncio
import json
import logging
from typing import Optional, Dict, Any

import aiohttp

# Import the protobuf messages (generated from esp_local_ctrl.proto)
from .esp_local_ctrl_pb2 import (
    LocalCtrlMessage,
    LocalCtrlMsgType,
    CmdGetPropertyCount,
    CmdGetPropertyValues,
    CmdSetPropertyValues,
    PropertyValue
)

_LOGGER = logging.getLogger(__name__)

class ESPLocalDevice:
    """ESP Local Control Device."""
    
    def __init__(self, host: str, port: int, node_id: str, pop: str, security_type: int):
        self.host = host
        self.port = port
        self.node_id = node_id
        self.pop = pop
        self.security_type = security_type
        self.base_url = f"http://{host}:{port}"
        self.control_path = "esp_local_ctrl/control"
        self.property_count = -1
        self._params_cache = {}
    
    async def _send_request(self, message: LocalCtrlMessage) -> Optional[LocalCtrlMessage]:
        """Send a protobuf request to the device."""
        url = f"{self.base_url}/{self.control_path}"
        payload = message.SerializeToString()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
            "Connection": "Keep-Alive"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        body = await response.read()
                        return LocalCtrlMessage.FromString(body)
                    else:
                        _LOGGER.error(f"HTTP error: {response.status}")
                        return None
        except Exception as e:
            _LOGGER.error(f"Failed to send request: {e}")
            return None
    
    async def get_property_count(self) -> int:
        """Get the number of properties."""
        if self.property_count > 0:
            return self.property_count
        
        message = LocalCtrlMessage(
            msg=LocalCtrlMsgType.TypeCmdGetPropertyCount,
            cmd_get_prop_count=CmdGetPropertyCount()
        )
        
        response = await self._send_request(message)
        if response and response.HasField('resp_get_prop_count'):
            self.property_count = response.resp_get_prop_count.count
            return self.property_count
        
        return -1
    
    async def get_property_values(self) -> Optional[Dict[str, Any]]:
        """Get all property values."""
        count = await self.get_property_count()
        if count <= 0:
            return None
        
        # Request all properties (indices 0 to count-1)
        message = LocalCtrlMessage(
            msg=LocalCtrlMsgType.TypeCmdGetPropertyValues,
            cmd_get_prop_vals=CmdGetPropertyValues(
                indices=list(range(count))
            )
        )
        
        response = await self._send_request(message)
        if not response or not response.HasField('resp_get_prop_vals'):
            return None
        
        properties = {}
        for prop_info in response.resp_get_prop_vals.props:
            try:
                # Decode the JSON value
                value_json = json.loads(prop_info.value.decode('utf-8'))
                properties[prop_info.name] = value_json
                
                # Cache params for quick access
                if prop_info.name == "params":
                    self._params_cache = value_json
                    
            except Exception as e:
                _LOGGER.error(f"Failed to parse property {prop_info.name}: {e}")
        
        return properties
    
    async def set_property_values(self, params_json: Dict[str, Any]) -> bool:
        """Set device parameters."""
        # Property at index 1 is "params" which contains device controls
        json_str = json.dumps(params_json)
        
        message = LocalCtrlMessage(
            msg=LocalCtrlMsgType.TypeCmdSetPropertyValues,
            cmd_set_prop_vals=CmdSetPropertyValues(
                props=[
                    PropertyValue(
                        index=1,  # Index 1 is always "params"
                        value=json_str.encode('utf-8')
                    )
                ]
            )
        )
        
        response = await self._send_request(message)
        if response and response.HasField('resp_set_prop_vals'):
            success = response.resp_set_prop_vals.status == 0  # 0 = Success
            if success:
                # Update cache
                for key, value in params_json.items():
                    if key in self._params_cache:
                        self._params_cache[key].update(value)
            return success
        
        return False
    
    async def get_params(self) -> Dict[str, Any]:
        """Get current device params (brightness, power, etc.)."""
        if not self._params_cache:
            properties = await self.get_property_values()
            if properties and "params" in properties:
                self._params_cache = properties["params"]
        
        return self._params_cache
    
    async def set_param(self, device_name: str, param_name: str, value: Any) -> bool:
        """Set a specific parameter."""
        # BG Smart dimmers use nested JSON: {"DeviceName": {"param": value}}
        params = {
            device_name: {
                param_name: value
            }
        }
        return await self.set_property_values(params)


