
import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
import itertools

from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
from OuchServer.ouch_server import nanoseconds_since_midnight

###
# TODOs:
##  - how should status be changing in order store?
##  - how should messages be sent?
##      can we just do the current communication channel approach?
##      
##      

DEFAULT_LIQUIDITY_FLAG = b'?'

order_ref_numbers = itertools.count(1, 2)  # odds

class Exchange:
    def __init__(self, order_book, order_reply):
        '''
        order_book - the book!
        order_reply - post office reply function, takes in 
                message 
                original order
                context
            and does whatever we need to get that info back to order sender                             
        '''
        self.order_store = {}
        self.order_book = order_book
        self.order_reply = order_reply
        self.next_match_number = 0

    async def process_message(self, message):
        if message.message_type is OuchClientMessages.EnterOrder:
            await self.enter_order(message)
        elif message.message_type is ReplaceOrder:
            await self.replace_order(message)
        elif message.message_type is CancelOrder:
            await self.cancel_order(message)
        elif message.message_type is ModifyOrder:
            await self.modify_order(message)
        elif message.message_type is TradeNow:
            raise NotImplementedError()
        else:
            raise NameError("Unknown message type.")

    async def enter_order(self, enter_order_message):
        self.order_store[ enter_order_message['order_token'] ] = enter_order_message
        fields = dict(enter_order_message.iteritems())
        fields['bbo_weight_indicator'] = b' '
        fields['order_reference_number'] = next(order_ref_numbers)
        fields['timestamp'] = nanoseconds_since_midnight()
        fields['order_state'] = b'L'
    
        #send order accepted (OUCH) message
        accepted_response = OuchServerMessages.Accepted(**fields)
        accepted_response.meta = enter_order_message.meta #TODO: eliminate having to do this
        await self.order_reply(accepted_response) 
        crossed_orders = []
        #enter order in book
        timestamp = nanoseconds_since_midnight()


        if enter_order_message['buy_sell_indicator'] == b'B':
            log.debug('Entering BUY order into order book')
            (crossed_orders, entered_order) = self.order_book.enter_limit_buy(
                    enter_order_message['order_token'],
                    enter_order_message['price'],
                    enter_order_message['shares'])
        else:   
            log.debug('Entering SELL order into order book')
            (crossed_orders, entered_order) = self.order_book.enter_limit_sell(
                    enter_order_message['order_token'],
                    enter_order_message['price'],
                    enter_order_message['shares'])
        #log.debug("Resulting book: %s", str(self.order_book))

        for ((id, fulfilling_order_id), price, volume) in crossed_orders:
            log.debug('Orders (%s, %s) crossed at price %s, volume %s', id, fulfilling_order_id, price, volume)
            assert id == enter_order_message['order_token']
            fulfilling_order_message = self.order_store[fulfilling_order_id]
            match_number = self.next_match_number
            self.next_match_number += 1
            r1 = OuchServerMessages.Executed(
                    timestamp = timestamp,
                    order_token = id,
                    executed_shares = volume,
                    execution_price = price,
                    liquidity_flag = DEFAULT_LIQUIDITY_FLAG,
                    match_number = match_number
                    )
            r1.meta = enter_order_message.meta
            r2 = OuchServerMessages.Executed(
                    timestamp = timestamp,
                    order_token = fulfilling_order_id,
                    executed_shares = volume,
                    execution_price = price,
                    liquidity_flag = DEFAULT_LIQUIDITY_FLAG,
                    match_number = match_number
                    )
            r2.meta = fulfilling_order_message.meta
            await self.order_reply(r1)
            await self.order_reply(r2)

    async def cancel_order(self, cancel_order_message):
        raise NotImplementedError()

    async def modify_order(self, modify_order_message):
        raise NotImplementedError()

    async def replace_order(self, replace_order_message):
        raise NotImplementedError()


def main():
    from functools import partial
    from OuchServer.ouch_server import ProtocolMessageServer
    from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
    from simple_order_book import SimpleOrderBook

    log.basicConfig(level=log.INFO)

    loop = asyncio.get_event_loop()
    server = ProtocolMessageServer(OuchClientMessages)
    book = SimpleOrderBook()
    exchange = Exchange(order_book = book,
                        order_reply = server.send_server_response)
    server.register_listener(exchange.process_message)
    server.start(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    main()
