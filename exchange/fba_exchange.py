import logging as log
import asyncio
from exchange.exchange import Exchange
from OuchServer.ouch_server import nanoseconds_since_midnight


class FBAExchange(Exchange):
    def __init__(self, interval, *args, **kwargs):
        self.interval = interval
        super().__init__(*args, **kwargs)

    def start(self):
        asyncio.ensure_future(self.run_batch_repeating())

    def run_batch_atomic(self):
        timestamp = nanoseconds_since_midnight()
        log.debug("Running batch at timestamp=%s", timestamp)
        crossed_orders = self.order_book.batch_process()
        cross_messages = [m for ((id, fulfilling_order_id), price, volume) 
                                            in crossed_orders 
                            for m in self.process_cross(
                                id, fulfilling_order_id, 
                                price, volume, 
                                timestamp=timestamp)]
        self.outgoing_messages.extend(cross_messages)

    async def run_batch_repeating(self):
        while True:
            self.run_batch_atomic()
            await self.send_outgoing_messages()
            await asyncio.sleep(self.interval)