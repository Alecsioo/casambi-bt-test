"""Expose Casambi scenes to Apple Home as HomeKit switches, without Home Assistant.

Each scene becomes a switch that turns itself off right after the scene fires,
so "Hey Siri, turn on <scene name>" triggers it.
"""
import argparse
import asyncio
import getpass
import json
import logging
import os
import signal
from dataclasses import dataclass
from pathlib import Path

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SWITCH

log = logging.getLogger("casambi-homekit")

CONFIG_FILE = Path(__file__).with_name("bridge_config.json")
STATE_FILE = str(Path(__file__).with_name("accessory.state"))
RESET_DELAY = 1.5
WATCHDOG_INTERVAL = 15
FIRST_SCENE_AID = 10


@dataclass
class DemoScene:
    sceneId: int
    name: str


class DemoCasambi:
    """Stands in for the Casambi network so the HomeKit side can be tried without lights."""

    connected = True
    scenes = [DemoScene(1, "Demo Bright"), DemoScene(2, "Demo Movie"), DemoScene(3, "Demo Off")]

    async def switchToScene(self, scene):
        log.info("[demo] scene fired: %s", scene.name)


class CasambiLink:
    """Keeps one Bluetooth connection to the Casambi network alive."""

    def __init__(self, address, password):
        from CasambiBt import Casambi

        self.address = address.upper()
        self.password = password
        self.casa = Casambi()
        self._lock = asyncio.Lock()

    @property
    def scenes(self):
        return self.casa.scenes

    async def _connect(self):
        from CasambiBt import discover

        devices = await discover()
        device = next((d for d in devices if d.address.upper() == self.address), None)
        if device is None:
            raise ConnectionError(f"Casambi device {self.address} not found over Bluetooth")
        await self.casa.connect(device, self.password)

    async def ensure_connected(self):
        async with self._lock:
            if self.casa.connected:
                return
            log.info("Connecting to Casambi network...")
            try:
                await self.casa.disconnect()
            except Exception:
                pass
            await self._connect()
            log.info("Connected.")

    async def switchToScene(self, scene):
        await self.ensure_connected()
        await self.casa.switchToScene(scene)

    async def watchdog(self):
        while True:
            await asyncio.sleep(WATCHDOG_INTERVAL)
            try:
                await self.ensure_connected()
            except Exception as err:
                log.warning("Reconnect failed, will retry: %s", err)


class SceneSwitch(Accessory):
    category = CATEGORY_SWITCH

    def __init__(self, driver, scene, network):
        super().__init__(driver, scene.name, aid=FIRST_SCENE_AID + scene.sceneId)
        self._scene = scene
        self._network = network
        service = self.add_preload_service("Switch")
        self._on = service.configure_char("On", setter_callback=self._set_on)

    def _set_on(self, value):
        if value:
            asyncio.run_coroutine_threadsafe(self._fire(), self.driver.loop)

    async def _fire(self):
        try:
            await self._network.switchToScene(self._scene)
        except Exception:
            log.exception("Could not switch to scene %s", self._scene.name)
        finally:
            await asyncio.sleep(RESET_DELAY)
            self._on.set_value(False)


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (OSError, ValueError):
        return {}


async def pick_device():
    from CasambiBt import discover

    print("Scanning for Casambi networks over Bluetooth...")
    devices = await discover()
    if not devices:
        raise SystemExit("No Casambi devices found. Check Bluetooth and close the Casambi phone app.")
    for i, dev in enumerate(devices):
        print(f"[{i}] {getattr(dev, 'name', '?')}  {dev.address}")
    return devices[int(input("Pick a device number: ") or 0)].address


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="fake scenes, no Casambi needed")
    parser.add_argument("--device", help="Casambi Bluetooth address (remembered after the first run)")
    parser.add_argument("--ip", help="IP of this PC on your home network, if pairing can't find the bridge")
    parser.add_argument("--port", type=int, default=51826)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if args.demo:
        network = DemoCasambi()
        link = None
    else:
        address = args.device or load_config().get("device") or loop.run_until_complete(pick_device())
        password = os.environ.get("CASAMBI_PASSWORD") or getpass.getpass("Network password (typed hidden): ")
        link = network = CasambiLink(address, password)
        loop.run_until_complete(link.ensure_connected())
        CONFIG_FILE.write_text(json.dumps({"device": address}))

    driver = AccessoryDriver(address=args.ip, port=args.port, persist_file=STATE_FILE, loop=loop)
    bridge = Bridge(driver, "Casambi")
    for scene in network.scenes:
        bridge.add_accessory(SceneSwitch(driver, scene, network))
    driver.add_accessory(accessory=bridge)

    if link:
        loop.create_task(link.watchdog())
    signal.signal(signal.SIGINT, driver.signal_handler)

    pin = driver.state.pincode.decode()
    log.info("%d scenes exposed. Pair in the Home app with code %s", len(network.scenes), pin)
    driver.start()


if __name__ == "__main__":
    main()
