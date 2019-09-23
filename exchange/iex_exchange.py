import logging as log
from exchange.exchange import Exchange
from OuchServer.ouch_server import nanoseconds_since_midnight
from OuchServer.ouch_messages import OuchClientMessages

class IEXExchange(Exchange):
    delayed_message_types = (
        OuchClientMessages.EnterOrder,
        OuchClientMessages.ReplaceOrder,
        OuchClientMessages.CancelOrder,
    )

    def __init__(self, delay, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delay = delay
        self.handlers.update({
            OuchClientMessages.ExternalFeedChange: self.external_feed_change,
        })
    
    async def process_message(self, message):
        if message.message_type in self.handlers:
            log.debug('Processing message %s', message)
        else:
            log.error("Unknown message type %s", message.message_type)
            return False

        if message.message_type in self.delayed_message_types:
            self.loop.call_later(self.delay, self._process_message, message)
        else:
            await self._process_message(message)

    async def _process_message(self, message):
        """actually process a message. called, possibly after a delay, by process_message"""
        timestamp = nanoseconds_since_midnight()
        self.handlers[message.message_type](message, timestamp)
        await self.send_outgoing_messages()

    def external_feed_change(self, message, timestamp):
        nbbo = (message['e_best_bid'] + message['e_best_offer']) / 2
        log.debug('NBBO Change: new NBBO is %d', nbbo)
        self.order_book.nbbo_update(nbbo)