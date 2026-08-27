#!/usr/bin/env python3
"""
GPS Spoof — persistent connection version.
Uses pymobiledevice3 Python API directly for fast joystick updates.

When --rsd <HOST> <PORT> is provided, the script connects via
RemoteServiceDiscoveryService. Otherwise it falls back to
PreferredRsdTunnel for the default local RSD flow.

Terminal 1 (optional): sudo python3 -m pymobiledevice3 remote start-tunnel
Terminal 2: python3 gps_spoof.py --rsd <HOST> <PORT>
Or without RSD arguments: python3 gps_spoof.py
Then open:  http://localhost:8765
"""

import argparse
import asyncio
import atexit
import json
import os
import signal
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler



# ── Dependency Check ──────────────────────────────────────────────────────────

def check_dependencies() -> bool:
    """Verify pymobiledevice3 is installed and meets version requirements (v11.x.x)."""
    try:
        import importlib.metadata
        ver_str = importlib.metadata.version('pymobiledevice3')
    except Exception:
        try:
            import pymobiledevice3
            ver_str = getattr(pymobiledevice3, '__version__', 'unknown')
        except ImportError:
            print("\n❌ Error: 'pymobiledevice3' is not installed.")
            print("   Please install it with:")
            if sys.platform == 'win32':
                print('     pip install "pymobiledevice3>=11.0.0,<12"')
            else:
                print('     pip3 install "pymobiledevice3>=11.0.0,<12"')
            print()
            return False

    try:
        major = int(ver_str.split('.')[0])
        if major < 11:
            print(f"\n⚠️  Error: Detected outdated 'pymobiledevice3' (version {ver_str}).")
            print("   GPS Spoof requires pymobiledevice3 version 11.x.x.")
            print("   Please upgrade by running:")
            if sys.platform == 'win32':
                print('     pip install --upgrade "pymobiledevice3>=11.0.0,<12"')
            else:
                print('     pip3 install --upgrade "pymobiledevice3>=11.0.0,<12"')
            print()
            return False
    except Exception:
        pass

    return True


# ── Device Discovery and Selection ────────────────────────────────────────────

async def get_device_info(serial: str, conn_type: str) -> dict:
    """Fetch friendly metadata for a single device via lockdown."""
    from pymobiledevice3.lockdown import create_using_usbmux

    try:
        ld = await asyncio.wait_for(
            create_using_usbmux(serial=serial, connection_type=conn_type),
            timeout=2.0
        )
        async with ld:
            info = ld.short_info or ld.all_values or {}
            return {
                'serial': serial,
                'connection_type': conn_type,
                'name': info.get('DeviceName') or 'iPhone',
                'product_type': info.get('ProductType') or '',
                'version': info.get('ProductVersion') or ''
            }
    except Exception:
        return {
            'serial': serial,
            'connection_type': conn_type,
            'name': 'iOS Device',
            'product_type': '',
            'version': ''
        }


async def discover_devices() -> list[dict]:
    """Discover all connected iOS devices across USB, Network, and macOS native pairing."""
    from pymobiledevice3.usbmux import list_devices

    devices: dict[str, dict] = {}

    # 1. Query usbmux devices (both USB and Network)
    try:
        raw_mux = await asyncio.wait_for(list_devices(), timeout=3.0)
        tasks = [get_device_info(d.serial, d.connection_type) for d in raw_mux]
        mux_results = await asyncio.gather(*tasks)
        for r in mux_results:
            s = r['serial']
            # Prioritize USB over Network if the device appears in both
            if s not in devices or r['connection_type'] == 'USB':
                devices[s] = r
    except Exception:
        pass

    # 2. On macOS, query remotepairingd native devices as supplement
    if sys.platform == 'darwin':
        try:
            from pymobiledevice3.remote.native_tunnel import browse_native_devices
            native_devs = await asyncio.wait_for(browse_native_devices(timeout=1.5), timeout=2.5)
            for nd in native_devs:
                udid = nd.get('udid')
                if not udid:
                    continue
                name = nd.get('name') or nd.get('UserAssignedDeviceName') or 'iPhone'
                product = nd.get('model') or nd.get('ProductType') or ''
                if udid not in devices:
                    devices[udid] = {
                        'serial': udid,
                        'connection_type': 'Network' if nd.get('wirelessConnectivity') else 'USB',
                        'name': name,
                        'product_type': product,
                        'version': ''
                    }
                elif devices[udid]['name'] in ('iPhone', 'iOS Device') and name not in ('iPhone', 'iOS Device'):
                    devices[udid]['name'] = name
                    if product:
                        devices[udid]['product_type'] = product
        except Exception:
            pass

    return list(devices.values())


# ── Last Connected Device Persistence ─────────────────────────────────────────

LAST_DEVICE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_device.json')


def load_last_device() -> dict | None:
    """Load metadata of the last successfully connected / selected device."""
    try:
        with open(LAST_DEVICE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and data.get('serial'):
                return data
    except (FileNotFoundError, json.JSONDecodeError, KeyError, Exception):
        pass
    return None


def save_last_device(device_info: dict | None):
    """Save metadata of the last connected / selected device."""
    if not device_info or not device_info.get('serial'):
        return
    try:
        with open(LAST_DEVICE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'serial': str(device_info['serial']),
                'name': str(device_info.get('name') or 'iOS Device'),
                'product_type': str(device_info.get('product_type') or ''),
                'version': str(device_info.get('version') or '')
            }, f, indent=2)
    except Exception:
        pass


def select_device(devices: list[dict], target_serial: str | None = None) -> dict | None:
    """
    Select target device from discovered list.
    - If target_serial is provided: match directly and remember it.
    - If last connected device is known: prioritize it as the default choice.
    - If exactly 1 device found: connect automatically and remember it.
    - If multiple devices found: prompt the user interactively with the last used device as default.
    - If 0 devices found: fallback to last connected device or attempt default connection.
    """
    last_device = load_last_device()

    if target_serial:
        target_serial_clean = target_serial.strip()
        for d in devices:
            if target_serial_clean.lower() in d['serial'].lower():
                print(f"  Target device selected via CLI: {d['name']} ({d['serial']}) [{d['connection_type']}]")
                save_last_device(d)
                return d
        print(f"  Target device serial: {target_serial_clean}")
        chosen = {'serial': target_serial_clean, 'name': 'Target Device', 'connection_type': 'USB', 'product_type': '', 'version': ''}
        save_last_device(chosen)
        return chosen

    if len(devices) == 0:
        if last_device:
            print("  ⚠️  No connected iOS devices detected via USB/Network.")
            print(f"     Will attempt connection to last used device: {last_device['name']} ({last_device['serial']})...")
            return {
                'serial': last_device['serial'],
                'name': last_device.get('name', 'Target Device'),
                'connection_type': 'USB',
                'product_type': last_device.get('product_type', ''),
                'version': last_device.get('version', '')
            }
        print("  ⚠️  No connected iOS devices detected via USB/Network.")
        print("     Will attempt default connection...")
        return None

    if len(devices) == 1:
        d = devices[0]
        model_str = f", {d['product_type']}" if d['product_type'] else ""
        print(f"  📱 1 device found: {d['name']} ({d['serial']}{model_str}) [{d['connection_type']}]")
        print("     Connecting automatically...")
        save_last_device(d)
        return d

    # Multiple devices found: if a last used device is present, sort it to position 1 as default
    last_serial = last_device['serial'].lower() if (last_device and last_device.get('serial')) else None
    if last_serial:
        matched_idx = next((i for i, d in enumerate(devices) if d['serial'].lower() == last_serial), None)
        if matched_idx is not None and matched_idx != 0:
            last_dev_obj = devices.pop(matched_idx)
            devices.insert(0, last_dev_obj)

    print(f"\n  📱 Multiple devices found ({len(devices)}):")
    for i, d in enumerate(devices, 1):
        model_str = f", {d['product_type']}" if d['product_type'] else ""
        ver_str = f" iOS {d['version']}" if d['version'] else ""
        is_last = bool(last_serial and d['serial'].lower() == last_serial)
        tag = " (last connected — default)" if is_last else ""
        print(f"    [{i}] {d['name']} ({d['serial']}{model_str}{ver_str}) [{d['connection_type']}]{tag}")

    print()
    while True:
        try:
            choice = input(f"  Select device [1-{len(devices)}] (default: 1): ").strip()
            if not choice:
                selected = devices[0]
                break
            idx = int(choice)
            if 1 <= idx <= len(devices):
                selected = devices[idx - 1]
                break
            print(f"  Please enter a number between 1 and {len(devices)}.")
        except ValueError:
            # Check if user typed or pasted part of a UDID or name
            matched = [d for d in devices if choice.lower() in d['serial'].lower() or choice.lower() in d['name'].lower()]
            if len(matched) == 1:
                selected = matched[0]
                break
            print(f"  Invalid selection '{choice}'. Please enter a number [1-{len(devices)}].")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

    print(f"  Selected: {selected['name']} ({selected['serial']})\n")
    save_last_device(selected)
    return selected


# ── Persistent Location Controller ────────────────────────────────────────────

class LocationController:
    """
    Maintains a single persistent connection to the device.
    set_location() is non-blocking and always uses the latest coordinate.
    """

    def __init__(self, rsd_host: str | None, rsd_port: int | None, serial: str | None = None, device_name: str | None = None):
        self.rsd_host = rsd_host
        self.rsd_port = rsd_port
        self.serial = serial
        self.device_name = device_name
        self.connected = False
        self.status = f'Connecting to {self.device_name}...' if self.device_name else 'Connecting to device...'
        self._latest: tuple | None = None
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._event: asyncio.Event | None = None

        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def set_location(self, lat: float, lon: float, alt: float | None = None):
        """Called from HTTP handler thread — non-blocking."""
        with self._lock:
            if alt is not None:
                self._latest = (lat, lon, alt)
            else:
                self._latest = (lat, lon)
        if self._loop and self._event and self._loop.is_running():
            try:
                self._loop.call_soon_threadsafe(self._event.set)
            except RuntimeError:
                pass

    def _run(self):
        asyncio.run(self._async_main())

    async def _async_main(self):
        from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
        from pymobiledevice3.remote.rsd_tunnel import PreferredRsdTunnel
        from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
        from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

        self._loop = asyncio.get_running_loop()
        self._event = asyncio.Event()

        try:
            if self.rsd_host is not None and self.rsd_port is not None:
                print(f'  Connecting to RSD at {self.rsd_host}:{self.rsd_port}...')
                rsd_service = RemoteServiceDiscoveryService((self.rsd_host, self.rsd_port))
            else:
                target_desc = f"{self.device_name} ({self.serial})" if self.device_name and self.serial else (self.device_name or self.serial or 'default device')
                print(f'  Connecting to {target_desc} via RSD tunnel...')
                rsd_service = PreferredRsdTunnel(serial=self.serial)

            async with rsd_service as rsd:
                async with DvtProvider(rsd) as dvt:
                    async with LocationSimulation(dvt) as loc:
                        self.connected = True
                        dev_label = self.device_name or 'Phone'
                        self.status = f'{dev_label} connected successfully'
                        print(f'  Device \'{dev_label}\' connected. Ready to spoof.')
                        if self.serial:
                            save_last_device({'serial': self.serial, 'name': self.device_name or dev_label})

                        last_sent: tuple | None = None
                        while True:
                            # Wait up to 1 s for a new location; on timeout, resend
                            # the last known coordinate to hold the GPS lock
                            try:
                                await asyncio.wait_for(self._event.wait(), timeout=1.0)
                                self._event.clear()
                            except asyncio.TimeoutError:
                                pass

                            with self._lock:
                                if self._latest is not None:
                                    last_sent = self._latest
                                    self._latest = None

                            if last_sent:
                                await loc.set(last_sent[0], last_sent[1])

        except Exception as e:
            self.connected = False
            self.status = 'Phone disconnected'
            print(f'  Connection error: {e}')
        finally:
            self.connected = False
            self._loop = None
            self._event = None
            print('\n  Device connection closed. Exiting...')
            os._exit(0)


controller: LocationController | None = None


# ── Favorites ──────────────────────────────────────────────────────────────────

FAVORITES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'favorites.json')
folders: list = []  # [{ "name": str, "spots": [{ "icon": str, "name": str, "lat": float, "lon": float }] }]

def load_favorites():
    global folders
    try:
        with open(FAVORITES_FILE) as f:
            data = json.load(f)
        if isinstance(data, list):  # migrate old flat format
            folders = [{'name': 'General', 'spots': data}]
        elif isinstance(data, dict) and 'folders' in data:
            folders = data['folders']
        else:
            folders = [{'name': 'General', 'spots': []}]
    except (FileNotFoundError, json.JSONDecodeError):
        folders = [{'name': 'General', 'spots': []}]

def save_favorites():
    with open(FAVORITES_FILE, 'w') as f:
        json.dump({'folders': folders}, f, indent=2)


# ── Last Position ───────────────────────────────────────────────────────────────

POSITION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_position.json')

_current_position: tuple[float, float] | None = None
_last_disk_write_time: float = 0.0
_position_dirty: bool = False
_position_timer: threading.Timer | None = None
_position_lock = threading.Lock()

POSITION_SAVE_INTERVAL = 3.0  # minimum seconds between disk writes while moving


def load_position() -> tuple[float, float]:
    global _current_position
    with _position_lock:
        if _current_position is not None:
            return _current_position
        try:
            with open(POSITION_FILE) as f:
                d = json.load(f)
                _current_position = (float(d['lat']), float(d['lon']))
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            _current_position = (37.7749, -122.4194)  # default: San Francisco
        return _current_position


def _write_position_to_disk():
    global _position_dirty, _last_disk_write_time, _position_timer
    with _position_lock:
        if _position_timer:
            _position_timer.cancel()
            _position_timer = None
        if not _position_dirty or _current_position is None:
            return
        lat, lon = _current_position
        _position_dirty = False
        _last_disk_write_time = time.time()

    try:
        with open(POSITION_FILE, 'w') as f:
            json.dump({'lat': lat, 'lon': lon}, f)
    except Exception:
        pass


def flush_position():
    """Flush pending position changes to disk immediately."""
    _write_position_to_disk()


atexit.register(flush_position)


def save_position(lat: float, lon: float, force: bool = False):
    global _current_position, _position_dirty, _position_timer, _last_disk_write_time
    now = time.time()
    with _position_lock:
        _current_position = (lat, lon)
        _position_dirty = True

        if force or (now - _last_disk_write_time >= POSITION_SAVE_INTERVAL):
            if _position_timer:
                _position_timer.cancel()
                _position_timer = None
            _position_dirty = False
            _last_disk_write_time = now
            should_write_now = True
        else:
            should_write_now = False
            if _position_timer is None:
                _position_timer = threading.Timer(POSITION_SAVE_INTERVAL, _write_position_to_disk)
                _position_timer.daemon = True
                _position_timer.start()

    if should_write_now:
        try:
            with open(POSITION_FILE, 'w') as f:
                json.dump({'lat': lat, 'lon': lon}, f)
        except Exception:
            pass


# ── HTML UI ───────────────────────────────────────────────────────────────────

HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')


def load_html() -> bytes:
    """Read the HTML UI file."""
    try:
        with open(HTML_FILE, 'rb') as f:
            return f.read()
    except Exception as e:
        return f"<h1>Error loading UI from {HTML_FILE}: {e}</h1>".encode('utf-8')


# ── Server Session Lock ────────────────────────────────────────────────────────
active_tab_id: str | None = None
active_tab_last_seen: float = 0.0
session_lock = threading.Lock()


# ── HTTP Server ────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/favorites':
            data = json.dumps({'folders': folders}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == '/position':
            lat, lon = load_position()
            data = json.dumps({'lat': lat, 'lon': lon}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(load_html())

    def do_POST(self):
        global active_tab_id, active_tab_last_seen
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        client_tab_id = body.get('tabId')

        if self.path == '/claim_session':
            with session_lock:
                active_tab_id = client_tab_id
                active_tab_last_seen = time.time()
            data = {'ok': True, 'active_tab_id': active_tab_id}
        elif self.path == '/status':
            with session_lock:
                now = time.time()
                if client_tab_id and (active_tab_id is None or (now - active_tab_last_seen > 10.0)):
                    active_tab_id = client_tab_id
                if client_tab_id and client_tab_id == active_tab_id:
                    active_tab_last_seen = now
                is_active = (client_tab_id == active_tab_id) if client_tab_id else True

            data = {
                'connected': controller.connected if controller else False,
                'status': controller.status if controller else 'No controller',
                'device_name': controller.device_name if controller else '',
                'is_active': is_active
            }
        elif self.path == '/favorites/add':
            fi = body.get('folderIdx', 0)
            if 0 <= fi < len(folders):
                folders[fi]['spots'].append({
                    'icon': body.get('icon', '📍'),
                    'name': body['name'],
                    'lat': body['lat'],
                    'lon': body['lon']
                })
                save_favorites()
            data = {'ok': True}
        elif self.path == '/favorites/delete':
            fi = body.get('folderIdx', 0)
            si = body.get('spotIdx', -1)
            if 0 <= fi < len(folders) and 0 <= si < len(folders[fi]['spots']):
                folders[fi]['spots'].pop(si)
                save_favorites()
            data = {'ok': True}
        elif self.path == '/folders/add':
            folders.append({'name': body.get('name', 'New Folder'), 'spots': []})
            save_favorites()
            data = {'ok': True}
        elif self.path == '/folders/rename':
            fi = body.get('folderIdx', -1)
            if 0 <= fi < len(folders):
                folders[fi]['name'] = body.get('name', folders[fi]['name'])
                save_favorites()
            data = {'ok': True}
        elif self.path == '/folders/delete':
            fi = body.get('folderIdx', -1)
            if 0 <= fi < len(folders) and len(folders) > 1:
                folders.pop(fi)
                save_favorites()
            data = {'ok': True}
        else:  # /jump
            with session_lock:
                is_allowed = (client_tab_id is None or active_tab_id is None or client_tab_id == active_tab_id)

            if is_allowed:
                lat, lon = body['lat'], body['lon']
                alt = body.get('alt')
                if controller:
                    controller.set_location(lat, lon, alt)
                save_position(lat, lon)
                data = {
                    'ok': True,
                    'status': controller.status if controller else 'ok'
                }
            else:
                data = {'ok': False, 'error': 'Tab inactive'}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def _free_port(port):
    """Kill any previous instance holding `port`. Cross-platform (macOS/Linux/Windows)."""
    import subprocess

    pids = []
    try:
        if sys.platform == 'win32':
            # netstat lists "...:port ... LISTENING  <pid>" as the last column.
            out = subprocess.run(['netstat', '-ano', '-p', 'TCP'],
                                 capture_output=True, text=True).stdout
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[1].endswith(f':{port}') and parts[3] == 'LISTENING':
                    pids.append(parts[4])
        else:
            out = subprocess.run(['lsof', '-ti', f':{port}'],
                                 capture_output=True, text=True).stdout
            pids = out.strip().split()
    except FileNotFoundError:
        # No lsof/netstat available; skip the convenience cleanup.
        return

    for pid in set(pids):
        print(f'  Stopping previous instance (PID {pid})...')
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
            else:
                os.kill(int(pid), signal.SIGTERM)
        except (ProcessLookupError, ValueError):
            pass


def open_browser(url: str, delay: float = 0.5):
    """Automatically open the default web browser to the specified URL after a short delay."""
    def _open():
        webbrowser.open(url)

    timer = threading.Timer(delay, _open)
    timer.daemon = True
    timer.start()


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if not check_dependencies():
        sys.exit(1)

    parser = argparse.ArgumentParser(description='GPS Spoof — iOS Location Simulator')
    parser.add_argument('--rsd', nargs=2, metavar=('HOST', 'PORT'),
                        help='RSD address and port from: sudo python3 -m pymobiledevice3 remote start-tunnel')
    parser.add_argument('--serial', '--udid', dest='serial', metavar='UDID',
                        help='Target device UDID / serial')
    parser.add_argument('--list-devices', action='store_true',
                        help='List connected iOS devices and exit')
    parser.add_argument('--no-browser', action='store_true',
                        help='Do not automatically open default web browser on startup')
    args = parser.parse_args()

    if args.list_devices:
        print("\n  Scanning for connected iOS devices...")
        devices = asyncio.run(discover_devices())
        if not devices:
            print("  No connected iOS devices found.\n")
        else:
            print(f"\n  Found {len(devices)} device(s):")
            for i, d in enumerate(devices, 1):
                model_str = f", {d['product_type']}" if d['product_type'] else ""
                ver_str = f" iOS {d['version']}" if d['version'] else ""
                print(f"    [{i}] {d['name']} ({d['serial']}{model_str}{ver_str}) [{d['connection_type']}]")
            print()
        sys.exit(0)

    rsd_host, rsd_port = None, None
    selected_serial = None
    selected_name = None

    if args.rsd:
        rsd_host, rsd_port = args.rsd[0], int(args.rsd[1])
    else:
        print("\n  Scanning for connected iOS devices...")
        devices = asyncio.run(discover_devices())
        chosen = select_device(devices, target_serial=args.serial)
        if chosen:
            selected_serial = chosen.get('serial')
            selected_name = chosen.get('name')

    load_favorites()
    controller = LocationController(rsd_host, rsd_port, serial=selected_serial, device_name=selected_name)

    port = 8765
    _free_port(port)
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(('localhost', port), Handler)

    url = f'http://localhost:{port}'
    if not args.no_browser:
        open_browser(url)

    print()
    print('  GPS Spoof is running!')
    print(f'  Open in browser → {url}')
    print()
    print('  Waiting for device connection...')
    print('  Press Ctrl+C to stop.')
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
