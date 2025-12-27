# Quick Installation Guide

## Prerequisites

Before you start, gather this information:

1. **Device IP Address** - Find in your router's DHCP list
2. **PoP Key** - Printed on device label (looks like: `AbCd1234`)

## Installation Steps

### 1. Install via HACS

#### Add Custom Repository

1. Open **HACS** in your Home Assistant
2. Click the **3 dots** (⋮) in the top right
3. Select **Custom repositories**
4. Enter:
   - **Repository**: `https://github.com/rrwood/HA_BGSmart_LocalCtl`
   - **Category**: `Integration`
5. Click **Add**

#### Install Integration

1. In HACS, click **Integrations**
2. Search for **"BG Smart Local Control"**
3. Click on it
4. Click **Download**
5. **Restart Home Assistant**

### 2. Configure the Integration

#### Find Your Device IP

**Option A - Router Method:**
1. Log into your router admin page
2. Find DHCP client list or connected devices
3. Look for device named "ESP" or similar
4. Note the IP address (e.g., `192.168.1.100`)

**Option B - Network Scanner:**
- Use an app like "Fing" or "Network Scanner"
- Scan your network
- Look for ESP devices

**Option C - From BG Smart App:**
- Some versions show IP in device settings

#### Get PoP Key

The PoP (Proof of Possession) key is required for secure communication:

1. **Check device label** - Usually on back or inside
2. **Format examples**:
   - `abcd1234`
   - `ABCD-1234-EFGH`
   - 8-16 characters
3. **Case sensitive** - Enter exactly as shown

#### Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for **"BG Smart Local Control"**
4. Enter configuration:

   ```
   Device IP Address: 192.168.1.100    (your device IP)
   Port: 8080                           (pre-filled, don't change)
   PoP Key: AbCd1234                    (from device label)
   Node ID: [leave empty]               (auto-discovered)
   ```

5. Click **Submit**

### 3. Verify Installation

If successful, you'll see:
- ✅ Integration added to Devices & Services
- ✅ Device card showing dimmer name (e.g., "Lounge")
- ✅ Light entity created (e.g., `light.lounge`)

### 4. Test Control

1. **Find your light**:
   - Go to **Settings** → **Devices & Services**
   - Click on **BG Smart Local Control**
   - Click on your device name

2. **Test controls**:
   - Toggle On/Off
   - Adjust brightness slider
   - Changes should be instant (<100ms)

## Troubleshooting

### "Cannot Connect to Device"

**Problem**: Integration fails to connect

**Solutions**:

1. **Verify IP address is correct**
   ```bash
   ping 192.168.1.100
   ```
   Should get responses

2. **Check port is 8080**
   - Default is 8080
   - Don't change unless you know it's different

3. **Verify PoP key**
   - Must match device label exactly
   - Check for typos
   - Case sensitive

4. **Check network**
   - Device and Home Assistant on same network
   - No VLANs or network isolation
   - Port 8080 not blocked by firewall

### Integration Added But No Entities

**Problem**: Integration succeeds but no light entities appear

**Solution**:
1. Check logs: **Settings** → **System** → **Logs**
2. Filter for: `bg_smart`
3. Look for error messages
4. Try **removing and re-adding** integration

### Brightness Control Not Working

**Problem**: Can turn on/off but brightness slider missing

**Solution**:
1. **Remove integration**
2. **Restart Home Assistant**
3. **Re-add integration**
4. Brightness should now appear

### Getting Help

1. **Check logs** first
2. **Search existing issues**: https://github.com/rrwood/HA_BGSmart_LocalCtl/issues
3. **Open new issue** with:
   - Home Assistant version
   - Integration version
   - Device model
   - Relevant logs (Settings → System → Logs)

## Advanced Configuration

### Static IP (Recommended)

Set a static IP or DHCP reservation for your dimmer:

**Why**: Prevents IP changes requiring reconfiguration

**How**:
1. Log into your router
2. Find DHCP settings
3. Add reservation for device MAC address
4. Assign permanent IP (e.g., `192.168.1.100`)

### Multiple Dimmers

To add multiple dimmers:

1. Add integration multiple times
2. Use different IP address for each
3. Each gets its own entity

### Custom Names

Rename entities in Home Assistant:

1. Go to **Settings** → **Devices & Services**
2. Click on device
3. Click on entity
4. Click gear icon (⚙️)
5. Change **Name** and **Entity ID**

## Next Steps

Once installed:

- ✅ Add to Lovelace dashboard
- ✅ Create automations
- ✅ Add to scenes
- ✅ Use with voice assistants (Alexa, Google Home)
- ✅ Integrate with other smart home devices

## Example Dashboard Card

```yaml
type: light
entity: light.lounge
name: Lounge Dimmer
icon: mdi:ceiling-light
```

## Example Automation

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
```

---

**That's it! Enjoy fast, local control of your BG Smart dimmers!** 🎉
