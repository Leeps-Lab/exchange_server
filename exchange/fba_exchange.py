import logging as log
import asyncio
from exchange.exchange import Exchange
from OuchServer.ouch_server import nanoseconds_since_midnight
from OuchServer.ouch_messages import OuchServerMessages


class FBAExchange(Exchange):
    def __init__(self, interval, *args, **kwargs):
        self.interval = interval
        super().__init__(*args, **kwargs)

    def start(self):
        asyncio.ensure_future(self.run_batch_repeating())

    def run_batch_atomic(self):
        timestamp = nanoseconds_since_midnight()
        crossed_orders, clearing_price = self.order_book.batch_process()
        cross_messages = [m for ((id, fulfilling_order_id), price, volume) 
                                            in crossed_orders 
                            for m in self.process_cross(
                                id, fulfilling_order_id, 
                                price, volume, 
                                timestamp=timestamp)]
        self.outgoing_messages.extend(cross_messages)
        best_bid, best_ask, next_bid, next_ask = self.order_book.bbo
        self.outgoing_broadcast_messages.append(
            OuchServerMessages.PostBatch(
                    timestamp=nanoseconds_since_midnight(),
                    stock=b'AMAZGOOG',
                    clearing_price=clearing_price,
                    transacted_volume=len(crossed_orders),
                    best_bid=best_bid,
                    best_ask=best_ask,
                    next_bid=next_bid,
                    next_ask=next_ask)
            )

    async def run_batch_repeating(self):
        while True:
            self.run_batch_atomic()
            await self.send_outgoing_messages()
            await self.send_outgoing_broadcast_messages()
            await asyncio.sleep(self.interval - (self.loop.time() % self.interval))