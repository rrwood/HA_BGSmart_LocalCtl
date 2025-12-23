# BG Smart Local Control - Home Assistant Integration Setup

## What We Discovered

From reverse engineering the BG Smart app, we found it uses **ESP Local Control** protocol:

### Protocol Details:
- **Endpoint**: `http://[device-ip]:80/esp_local_ctrl/control`
- **Method**: HTTP POST with Protocol Buffer (protobuf) messages
- **Security**: Supports sec0 (no encryption) and sec1 (encrypted with PoP)
- **Properties**: 
  - Index 0: `config` - Device configuration (node_id, firmware, etc.)
  - Index 1: `params` - Device controls (brightness, power, etc.)

### Message Flow:
```
1. Get Property Count → Returns 2 (config + params)
2. Get Property Values → Returns JSON data for each property
3. Set Property Values → Send JSON to control device
```

### JSON Structure for Controls:
```json
{
  "DeviceName": {
    "Power": {"power": 1},
    "Brightness": {"brightness": 75}
  }
}
```

## Installation Steps

### 1. Create Directory Structure

```bash
cd /config
mkdir -p custom_components/bg_smart_local
cd custom_components/bg_smart_local
```

### 2. Install Required Files

Create these files in `custom_components/bg_smart_local/`:

- `__init__.py` - Main integration
- `manifest.json` - Integration metadata  
- `config_flow.py` - Configuration UI
- `esp_local_control.py` - Protocol implementation
- `light.py` - Light entity
- `strings.json` - UI strings
- `esp_local_ctrl.proto` - Protobuf definition

(All files are provided in the artifacts above)

### 3. Generate Protobuf Python Files

You need to compile the `.proto` file to Python:

```bash
# Install protobuf compiler
pip install protobuf grpcio-tools

# Generate Python code from .proto file
cd /config/custom_components/bg_smart_local
python -m grpc_tools.protoc -I. --python_out=. esp_local_ctrl.proto
```

This creates `esp_local_ctrl_pb2.py` which is imported by the integration.

### 4. Find Your Device

Your dimmer needs to be on the same network. Find its IP:

**Method 1: Router's DHCP list**
- Log into your router
- Look for "ESP" device or check connected devices

**Method 2: Network scanner**
```bash
# Using nmap
nmap -sn 192.168.1.0/24

# Or use Angry IP Scanner (GUI)
```

**Method 3: mDNS discovery**
The device advertises as `_esplocal._tcp` service:
```bash
# On Linux/Mac
avahi-browse -r _esplocal._tcp

# Or use Discovery app on Android
```

### 5. Test Connection

Before setting up Home Assistant, test the connection:

```bash
curl -X POST http://YOUR_DEVICE_IP/esp_local_ctrl/control \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-binary @get_count.bin
```

Where `get_count.bin` is the protobuf-encoded GetPropertyCount message.

### 6. Add Integration in Home Assistant

1. Restart Home Assistant
2. Go to **Settings** → **Devices & Services**
3. Click **Add Integration**
4. Search for "BG Smart Local Control"
5. Enter your device details:
   - **IP Address**: Device IP (e.g., 192.168.1.100)
   - **Port**: 80 (default)
   - **Node ID**: Leave blank (discovered automatically)
   - **PoP**: Leave blank if using sec0 security
   - **Security Type**: 0 (for sec0/no encryption)

### 7. Configure the Dimmer

Once added, the dimmer will appear as a light entity. You can:
- Turn on/off
- Adjust brightness (0-100%)
- Use in automations

## Understanding Device Parameters

The dimmer's params structure looks like this:

```json
{
  "Switch 1": {
    "Power": {
      "power": 1
    },
    "Brightness": {
      "brightness": 75
    }
  }
}
```

Where:
- `"Switch 1"` = Device name (may vary)
- `Power.power` = 0 (off) or 1 (on)
- `Brightness.brightness` = 0-100 (percentage)

## Troubleshooting

### Can't Connect to Device

1. **Check same network**: Device and HA must be on same WiFi
2. **Check firewall**: Ensure port 80 is not blocked
3. **Check IP address**: Device IP may have changed (use DHCP reservation)
4. **Try from terminal**: `ping YOUR_DEVICE_IP`

### Device Found But Won't Control

1. **Check security type**: If device uses sec1, you need the PoP key
2. **Check device name**: The device name in params must match
3. **Check logs**: Settings → System → Logs → Filter "bg_smart"

### Finding the PoP (Proof of Possession)

If device uses sec1 security, you need the PoP key:
- Usually printed on device label
- May be MAC address or serial number
- Check the BG Smart app settings

### Device Name Unknown

To find the actual device name:

1. Get property values manually:
```python
import asyncio
from esp_local_control import ESPLocalDevice

async def test():
    device = ESPLocalDevice("192.168.1.100", 80, "", "", 0)
    params = await device.get_params()
    print(params)

asyncio.run(test())
```

2. Look for device names in the output

## Advanced Configuration

### Multiple Dimmers

Add each dimmer separately with its own IP address. They'll all appear as separate light entities.

### Automation Example

```yaml
automation:
  - alias: "Dim lights at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.bg_smart_switch_1
        data:
          brightness_pct: 30
```

### Security Level 1 (Encrypted)

If your device uses sec1 security:

```python
# When adding integration, set:
Security Type: 1
PoP: "your_pop_key_here"
```

The PoP key is usually:
- Printed on device
- Last 8 digits of MAC address
- Check app settings

## Network Performance

- **Latency**: ~50-100ms (local network)
- **Polling interval**: Default 30 seconds
- **Reliability**: Very high (no cloud dependency)

## Comparison: Cloud API vs Local Control

| Feature | Cloud API | Local Control |
|---------|-----------|---------------|
| Latency | 500ms-2s | 50-100ms |
| Internet required | Yes | No |
| Reliability | Medium | High |
| Privacy | Data to cloud | All local |
| Setup complexity | OAuth | IP address |

**Recommendation**: Use local control for better performance and privacy!

## Protocol Documentation

For developers wanting to understand the protocol:

1. **ESP Local Control Official**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_local_ctrl.html

2. **Protobuf Messages**: See `esp_local_ctrl.proto`

3. **Request Flow**:
```
Client                          Device
  |                               |
  |-- Get Property Count -------->|
  |<------ Count = 2 -------------|
  |                               |
  |-- Get Properties [0,1] ------>|
  |<------ JSON data -------------|
  |                               |
  |-- Set Property [1] ---------->|
  |<------ Success ---------------|
```

## Next Steps

1. ✅ Device discovered and connected
2. ✅ Light entity created
3. ✅ Can control via UI
4. ⏭️ Add to dashboard
5. ⏭️ Create automations
6. ⏭️ Enjoy local control!

## Support

If you need help:
1. Check Home Assistant logs
2. Verify network connectivity
3. Test with curl commands
4. Open GitHub issue with logs

## Credits

Protocol reverse-engineered from BG Smart Android app.
Based on Espressif's ESP Local Control protocol.
