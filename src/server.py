import asyncio
from pyee.asyncio import AsyncIOEventEmitter
from services.events import events
from services.bluetooth import BluetoothService 
from services.asset_player import AssetPlaybackService
from services.audio_routing import AudioRoutingService
from services.voice_delegate import VoiceDelegateService

BL_MAC="EC:30:B3:2F:0E:FD"

bus = AsyncIOEventEmitter()


class CallService:
    def __init__(self, mac_addr: str):
        self.bluetooth = BluetoothService(mac_addr)
        self.STATE_HANDLERS = {
            "incoming": self.handle_incoming,
            "active": self.handle_active,
            "disconnected": self.stop
        }
        bus.on("hangup_active_call", lambda: self.bluetooth.hangup_active_call())

    async def stop(self, _):
        bus.emit(events["disconnected"])

    async def start(self):
        await self.bluetooth.listen_call_events(self.listen_callback)

    async def listen_callback(self, callpath, props):
        handler = self.STATE_HANDLERS.get(props['State'], self.pass_callback)
        await handler(callpath)

    async def handle_incoming(self, callpath):
        try:
            await asyncio.sleep(1)
            print("[info] answering the call")
            self.bluetooth.answer_call(callpath)

            await asyncio.sleep(2)

            bus.emit(events["start_vds"])
            bus.emit(events["remove_loopbacks"])
            await asyncio.sleep(1)
            # bus.emit(events["play_asset"], "leave_a_message")

            
        except Exception as e:
            print("Exception occured: ", e)
            bus.emit(events["play_asset"], "leave_a_message")
            bus.emit(events["stop_vds"])

            await asyncio.sleep(5)
            self.bluetooth.hangup_active_call()

    async def handle_active(self, callpath):
        pass

    async def pass_callback(self, callpath):
        pass

async def main():
    AssetPlaybackService(bus)
    VoiceDelegateService(bus)
    AudioRoutingService(bus, BL_MAC)
    call_handler = CallService(BL_MAC)
    await call_handler.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass