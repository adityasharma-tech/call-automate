import asyncio
import time
from pyee.asyncio import AsyncIOEventEmitter

bus = AsyncIOEventEmitter()


class TemperatureSensor:
    async def start(self):
        while True:
            await asyncio.sleep(2)

            payload = {
                "value": 25,
                "published_at": time.perf_counter_ns(),
            }

            print("Publishing temperature")
            bus.emit("temperature", payload)


class AlarmService:
    def __init__(self):
        bus.on("temperature", self.handle_temp)

    async def handle_temp(self, data):
        latency_ns = time.perf_counter_ns() - data["published_at"]

        print(
            f"Alarm received: {data['value']} "
            f"(latency={latency_ns:,} ns, {latency_ns/1000:.1f} µs)"
        )

        if data["value"] > 20:
            bus.emit(
                "warning",
                {
                    "message": "High temperature",
                    "published_at": time.perf_counter_ns(),
                },
            )


class NotificationService:
    def __init__(self):
        bus.on("warning", self.handle_warning)

    async def handle_warning(self, data):
        latency_ns = time.perf_counter_ns() - data["published_at"]

        print(
            f"NOTIFICATION: {data['message']} "
            f"(latency={latency_ns:,} ns, {latency_ns/1000:.1f} µs)"
        )


async def main():
    AlarmService()
    NotificationService()

    sensor = TemperatureSensor()

    await sensor.start()


asyncio.run(main())