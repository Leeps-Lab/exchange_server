import asyncio
import logging as log
from functools import partial
from exchange.exchange import Exchange
from OuchServer.ouch_server import nanoseconds_since_midnight
from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
from .order_books.cda_book import MIN_BID, MAX_ASK

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
        if message.message_type not in self.handlers:
            log.error("Unknown message type %s", message.message_type)
            return False
        log.debug('Processing message %s', message)

        if message.message_type in self.delayed_message_types:
            self.loop.call_later(self.delay, self._process_message, message)
        else:
            self._process_message(message)

    def _process_message(self, message):
        """actually process a message. called, possibly after a delay, by process_message"""
        timestamp = nanoseconds_since_midnight()
        self.handlers[message.message_type](message, timestamp)
        asyncio.ensure_future(self.send_outgoing_messages())
        asyncio.ensure_future(self.send_outgoing_broadcast_messages())

    def external_feed_change(self, message, timestamp):
        if message['e_best_bid'] == MIN_BID or message['e_best_offer'] >= MAX_ASK:
            peg_point = None
        else:
            peg_point = (message['e_best_bid'] + message['e_best_offer']) // 2
        log.debug('Peg update: new peg is is %d', peg_point)
        (crossed_orders, new_bbo) = self.order_book.update_peg_price(peg_point)
        cross_messages = [m for ((id, fulfilling_order_id), price, volume) in crossed_orders 
                            for m in self.process_cross(id, fulfilling_order_id, price, volume, timestamp=timestamp)]
        self.outgoing_messages.extend(cross_messages)
        if new_bbo:
            bbo_message = self.best_quote_update(message, new_bbo, timestamp)
            self.outgoing_broadcast_messages.append(bbo_message)

    # kind of a bummer that so much of this has to be repeated, but I can't think of a better way
    def enter_order_atomic(self, enter_order_message, timestamp, executed_quantity = 0):
        order_stored = self.order_store.store_order( 
            id = enter_order_message['order_token'], 
            message = enter_order_message, 
            executed_quantity = executed_quantity)
        if not order_stored:
            log.debug('Order already stored with id %s, order ignored', enter_order_message['order_token'])
            return []
        else:
            time_in_force = enter_order_message['time_in_force']
            enter_into_book = True if time_in_force > 0 else False    
            if time_in_force > 0 and time_in_force < 99998:     #schedule a cancellation at some point in the future
                cancel_order_message = self.cancel_order_from_enter_order( enter_order_message )
                self.loop.call_later(time_in_force, partial(self.cancel_order_atomic, cancel_order_message, timestamp))
            
            enter_order_func = self.order_book.enter_buy if enter_order_message['buy_sell_indicator'] == b'B' else self.order_book.enter_sell
            (crossed_orders, entered_order, new_bbo) = enter_order_func(
                    enter_order_message['order_token'],
                    enter_order_message['price'],
                    enter_order_message['shares'],
                    enter_into_book,
                    enter_order_message['midpoint_peg'])
            log.debug("Resulting book: %s", self.order_book)
            m=self.accepted_from_enter(enter_order_message, 
                order_reference_number=next(self.order_ref_numbers),
                timestamp=timestamp)
            self.order_store.add_to_order(m['order_token'], m)
            self.outgoing_messages.append(m)
            cross_messages = [m for ((id, fulfilling_order_id), price, volume) in crossed_orders 
                                for m in self.process_cross(id, fulfilling_order_id, price, volume, timestamp=timestamp)]
            self.outgoing_messages.extend(cross_messages)
            if new_bbo:
                bbo_message = self.best_quote_update(enter_order_message, new_bbo, timestamp)
                self.outgoing_broadcast_messages.append(bbo_message)

    def cancel_order_atomic(self, cancel_order_message, timestamp, reason=b'U'):
        if cancel_order_message['order_token'] not in self.order_store.orders:
            log.debug('No such order to cancel, ignored')
        else:
            store_entry = self.order_store.orders[cancel_order_message['order_token']]
            original_enter_message = store_entry.original_enter_message
            cancelled_orders, new_bbo = self.order_book.cancel_order(
                order_id = cancel_order_message['order_token'],
                price = store_entry.first_message['price'],
                volume = cancel_order_message['shares'],
                buy_sell_indicator = original_enter_message['buy_sell_indicator'],
                midpoint_peg = original_enter_message['midpoint_peg'])
            cancel_messages = [  self.order_cancelled_from_cancel(original_enter_message, timestamp, amount_canceled, reason)
                        for (id, amount_canceled) in cancelled_orders ]

            self.outgoing_messages.extend(cancel_messages) 
            log.debug("Resulting book: %s", self.order_book)
            if new_bbo:
                bbo_message = self.best_quote_update(cancel_order_message, new_bbo, timestamp)
                self.outgoing_broadcast_messages.append(bbo_message)

    # replace for iex is a little weird, right now it maintains the litness of any replaced order.
    # it doesn't really make sense to replace a pegged order at all for our implementation, so this should work fine.
    # however, if different peg points are added later this may need to be rethought
    def replace_order_atomic(self, replace_order_message, timestamp):
        if replace_order_message['existing_order_token'] not in self.order_store.orders:
            log.debug('Existing token %s unknown, siliently ignoring', replace_order_message['existing_order_token'])
            return []
        elif replace_order_message['replacement_order_token'] in self.order_store.orders:
            log.debug('Replacement token %s unknown, siliently ignoring', replace_order_message['existing_order_token'])
            return []
        else:
            store_entry = self.order_store.orders[replace_order_message['existing_order_token']]
            original_enter_message = store_entry.original_enter_message
            log.debug('store_entry: %s', store_entry)
            cancelled_orders, new_bbo_post_cancel = self.order_book.cancel_order(
                order_id = replace_order_message['existing_order_token'],
                price = store_entry.first_message['price'],
                volume = 0,
                buy_sell_indicator = original_enter_message['buy_sell_indicator'],
                midpoint_peg=original_enter_message['midpoint_peg'])  # Fully cancel
            
            if len(cancelled_orders)==0:
                log.debug('No orders cancelled, siliently ignoring')
                return []
            else:
                (id_cancelled, amount_cancelled) = cancelled_orders[0]
                first_message = store_entry.first_message
                shares_diff = replace_order_message['shares'] - first_message['shares'] 
                liable_shares = max(0, amount_cancelled + shares_diff )
                if liable_shares == 0:
                    log.debug('No remaining liable shares on the book to replace')
                    #send cancel
                else:
                    self.order_store.store_order(
                            id = replace_order_message['replacement_order_token'], 
                            message = replace_order_message,
                            original_enter_message = original_enter_message)
                    time_in_force = replace_order_message['time_in_force']
                    enter_into_book = True if time_in_force > 0 else False    
                    if time_in_force > 0 and time_in_force < 99998:     #schedule a cancellation at some point in the future
                        cancel_order_message = self.cancel_order_from_replace_order( replace_order_message )
                        self.loop.call_later(time_in_force, partial(self.cancel_order_atomic, cancel_order_message, timestamp))
                    
                    enter_order_func = self.order_book.enter_buy if original_enter_message['buy_sell_indicator'] == b'B' else self.order_book.enter_sell
                    crossed_orders, entered_order, new_bbo_post_enter = enter_order_func(
                            replace_order_message['replacement_order_token'],
                            replace_order_message['price'],
                            liable_shares,
                            enter_into_book,
                            midpoint_peg=original_enter_message['midpoint_peg'])
                    log.debug("Resulting book: %s", self.order_book)

                    r = OuchServerMessages.Replaced(
                            timestamp=timestamp,
                            replacement_order_token = replace_order_message['replacement_order_token'],
                            buy_sell_indicator=original_enter_message['buy_sell_indicator'],
                            shares=liable_shares,
                            stock=original_enter_message['stock'],
                            price=replace_order_message['price'],
                            time_in_force=replace_order_message['time_in_force'],
                            firm=original_enter_message['firm'],
                            display=replace_order_message['display'],
                            order_reference_number=next(self.order_ref_numbers), 
                            capacity=b'*',
                            intermarket_sweep_eligibility = replace_order_message['intermarket_sweep_eligibility'],
                            minimum_quantity = replace_order_message['minimum_quantity'],
                            cross_type=b'*',
                            order_state=b'L' if entered_order is not None else b'D',
                            previous_order_token=replace_order_message['existing_order_token'],
                            bbo_weight_indicator=b'*',
                            midpoint_peg=original_enter_message['midpoint_peg']
                            )
                    r.meta = replace_order_message.meta
                    self.outgoing_messages.append(r)
                    self.order_store.add_to_order(r['replacement_order_token'], r)        
                    cross_messages = [m for ((id, fulfilling_order_id), price, volume) in crossed_orders 
                                        for m in self.process_cross(id, 
                                                    fulfilling_order_id, 
                                                    price, 
                                                    volume, 
                                                    timestamp=timestamp)]
                    self.outgoing_messages.extend(cross_messages)

                    bbo_message = None
                    if new_bbo_post_enter:
                        bbo_message = self.best_quote_update(replace_order_message, 
                            new_bbo_post_enter, timestamp)
                    elif new_bbo_post_cancel:
                        bbo_message = self.best_quote_update(replace_order_message, 
                            new_bbo_post_cancel, timestamp)
                    if bbo_message:
                        self.outgoing_broadcast_messages.append(bbo_message)