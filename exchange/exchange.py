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
    def __init__(self, order_book, order_reply, loop):
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
        self.loop = loop

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
        timestamp = nanoseconds_since_midnight()
        self.order_store[ enter_order_message['order_token'] ] = enter_order_message
        fields = dict(enter_order_message.iteritems())
        fields['bbo_weight_indicator'] = b' '
        fields['order_reference_number'] = next(order_ref_numbers)
        fields['timestamp'] = timestamp
        fields['order_state'] = b'L'
    
        time_in_force = fields['time_in_force']
        print(time_in_force)
        enter_into_book = True if time_in_force > 0 else False
    
        if time_in_force > 0 and time_in_force < 99998:
            raise NotImplementedError
            #schedule a cancellation at some point in the future
            #99998 and 99999 are treated as run forever until close
            #cancel_order_message = cancel_order_from_enter_order( enter_order_message )
            self.loop.call_soon(time_in_force, self.cancel_order( cancel_order_message))
        
        if enter_order_message['buy_sell_indicator'] == b'B':
            log.debug('Entering BUY order into order book')
            (crossed_orders, entered_order) = self.order_book.enter_buy(
                    enter_order_message['order_token'],
                    enter_order_message['price'],
                    enter_order_message['shares'],
                    enter_into_book)
        else:   
            log.debug('Entering SELL order into order book')
            (crossed_orders, entered_order) = self.order_book.enter_sell(
                    enter_order_message['order_token'],
                    enter_order_message['price'],
                    enter_order_message['shares'],
                    enter_into_book)

        #send order accepted (OUCH) message
        #TODO - when should order response should be order_status='dead'
        accepted_response = OuchServerMessages.Accepted(**fields)
        accepted_response.meta = enter_order_message.meta
        await self.order_reply(accepted_response) 
        crossed_orders = []
        #enter order in book

        log.debug("Resulting book: %s", self.order_book)

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
        timestamp = nanoseconds_since_midnight()
        #do something to the order store - maybe delete order?
        self.order_book.cancel_order(cancel_order_message['order_token'])
        raise NotImplementedError()
        #send order cancelled message if successful

    async def modify_order(self, modify_order_message):
        raise NotImplementedError()

    async def replace_order(self, replace_order_message):
        raise NotImplementedError()
