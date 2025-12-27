# BG Smart Local Control for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/rrwood/HA_BGSmart_LocalCtl.svg)](https://github.com/rrwood/HA_BGSmart_LocalCtl/releases)
[![License](https://img.shields.io/github/license/rrwood/HA_BGSmart_LocalCtl.svg)](LICENSE)

Local control integration for BG Smart (Luceco) dimmer switches using the ESP Local Control protocol.

## Features

✅ **100% Local Control** - No cloud dependency, works without internet  
✅ **Fast Response** - 50-100ms latency vs 500ms-2s for cloud  
✅ **Privacy Friendly** - All communication stays on your local network  
✅ **Full Brightness Control** - On/Off and 0-100% dimming  
✅ **Auto Discovery** - Automatically finds and configures your dimmers  
✅ **Secure** - Uses Sec1 encryption with PoP (Proof of Possession)  

## Supported Devices

- BG Smart Dimmer Switch (DMHCM)
- Luceco Dimmer Controller
- Any ESP32-based BG Smart/Luceco device with local control

## Requirements

- Home Assistant 2024.1.0 or newer
- BG Smart dimmer on the same local network
- PoP (Proof of Possession) key from device label

## Installation

### Method 1: HACS (Recommended)

1. **Add Custom Repository**
   - Open HACS in Home Assistant
   - Click the 3 dots in top right → **Custom repositories**
   - Add repository URL: `https://github.com/rrwood/HA_BGSmart_LocalCtl`
   - Category: **Integration**
   - Click **Add**

2. **Install Integration**
   - Search for "BG Smart Local Control" in HACS
   - Click **Download**
   - Restart Home Assistant

3. **Add Integration**
   - Go to **Settings** → **Devices & Services**
   - Click **Add Integration**
   - Search for "BG Smart Local Control"
   - Follow configuration steps below

### Method 2: Manual Installation

1. **Download Files**
   ```bash
   cd /config
   git clone https://github.com/rrwood/HA_BGSmart_LocalCtl.git
   cp -r HA_BGSmart_LocalCtl/custom_components/bg_smart_local custom_components/
   ```

2. **Restart Home Assistant**

3. **Add Integration** (see configuration below)

## Configuration

### Step 1: Find Your Device Information

Before configuring, you need:

1. **Device IP Address**
   - Check your router's DHCP client list
   - Or use a network scanner app
   - Recommended: Set a static IP or DHCP reservation

2. **PoP (Proof of Possession) Key**
   - Printed on the device label
   - **Also shown as "Device ID" in BG Smart app** → Device Settings screen
   - Usually a string of characters/numbers (8-16 characters)

### Step 2: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "BG Smart Local Control"
4. Enter configuration:
   - **Device IP Address**: Your dimmer's IP (e.g., `192.168.1.100`)
   - **Port**: `8080` (default, pre-filled)
   - **PoP Key**: From device label (required)
   - **Node ID**: Leave empty (optional, auto-discovered)

5. Click **Submit**

### Step 3: Verify

The integration will:
- ✅ Connect to your dimmer
- ✅ Discover device name (e.g., "Lounge")
- ✅ Create light entity (e.g., `light.lounge`)
- ✅ Show current on/off state and brightness

## Usage

### Basic Control

The dimmer appears as a standard Home Assistant light entity:

```yaml
# Turn on at 50% brightness
service: light.turn_on
target:
  entity_id: light.lounge
data:
  brightness_pct: 50

# Turn off
service: light.turn_off
target:
  entity_id: light.lounge
```

### Automations

```yaml
automation:
  - alias: "Dim lights at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.lounge
        data:
          brightness_pct: 30

  - alias: "Lights off at bedtime"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: light.turn_off
        target:
          entity_id: light.lounge
```

### Scenes

```yaml
scene:
  - name: Movie Time
    entities:
      light.lounge:
        state: on
        brightness_pct: 20
```

### Dashboard Card

```yaml
type: light
entity: light.lounge
name: Lounge Dimmer
```

## Troubleshooting

### Cannot Connect to Device

**Check IP Address:**
```bash
ping 192.168.1.100  # Replace with your device IP
```

**Verify Port:**
- Default port is `8080`
- Device must be on same network as Home Assistant

**Check PoP Key:**
- Must match exactly from device label
- Case-sensitive
- No spaces

### Device Found But No Control

**Check Logs:**
```
Settings → System → Logs → Filter "bg_smart"
```

**Common Issues:**
- Wrong PoP key → Re-configure integration
- Network firewall blocking port 8080
- Device firmware outdated

### Brightness Not Working

**Delete and Re-add:**
1. Remove integration
2. Restart Home Assistant
3. Re-add integration

### Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.bg_smart_local: debug
```

Restart and check logs.

## Technical Details

### Protocol

- **Base Protocol**: ESP Local Control (Espressif)
- **Transport**: HTTP POST with Protocol Buffers
- **Port**: 8080 (HTTPS)
- **Security**: Sec1 (Curve25519 + AES-256-CTR)
- **Authentication**: PoP (Proof of Possession) key

### Communication

```
Home Assistant                    BG Smart Dimmer
      |                                  |
      |--- Get Property Count --------->|
      |<--- Count = 2 -------------------|
      |                                  |
      |--- Get Property Values -------->|
      |<--- Device State ----------------|
      |     (Power: True, Brightness: 48)|
      |                                  |
      |--- Set Property Values -------->|
      |     (Brightness: 75)             |
      |<--- Success --------------------|
```

### Update Frequency

- Polling interval: 30 seconds
- Immediate update on command
- Configurable in future versions

## Comparison: Local vs Cloud

| Feature | Local Control | Cloud API |
|---------|--------------|-----------|
| Latency | 50-100ms | 500ms-2s |
| Internet Required | ❌ No | ✅ Yes |
| Reliability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Privacy | ✅ All local | ❌ Data to cloud |
| Setup | IP + PoP | OAuth + Credentials |
| Works Offline | ✅ Yes | ❌ No |

## FAQ

**Q: Where do I find the PoP key?**  
A: It's printed on a label on the device, usually on the back or inside. It may be labeled as "PoP", "Proof of Possession", or "Security Key".

**Q: Can I control multiple dimmers?**  
A: Yes! Add each dimmer as a separate integration with its own IP address.

**Q: Does this work with BG Smart plugs or other devices?**  
A: Currently optimized for dimmers. Other device types may work but are untested.

**Q: What if I don't have the PoP key?**  
A: Check the BG Smart mobile app settings - it may display the PoP key. Otherwise, you'll need to contact BG Smart support.

**Q: Does this interfere with the BG Smart app?**  
A: No, both can be used simultaneously. Changes made in either app or Home Assistant will be reflected in both.

**Q: Can I use this without the BG Smart cloud?**  
A: Yes! This integration works completely independently of BG Smart cloud services.

## Support

- **Issues**: [GitHub Issues](https://github.com/rrwood/HA_BGSmart_LocalCtl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rrwood/HA_BGSmart_LocalCtl/discussions)
- **Home Assistant Community**: [Community Thread](https://community.home-assistant.io/)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Credits

- Protocol reverse-engineered from BG Smart Android app
- Based on [ESP Local Control](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_local_ctrl.html) by Espressif

## License

MIT License - See [LICENSE](LICENSE) file for details

## Disclaimer

This integration is not affiliated with, endorsed by, or connected to BG Electrical or Luceco. All product names, logos, and brands are property of their respective owners.

---

**Enjoy fast, local, and private control of your BG Smart dimmers!** ⚡
