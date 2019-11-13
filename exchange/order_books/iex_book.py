from collections import OrderedDict
import logging as log
from .cda_book import CDABook, bbo

class IEXBook(CDABook):

    def __init__(self):
        super().__init__()

        self.peg_price = None
        self.pegged_bids = OrderedDict()
        self.pegged_asks = OrderedDict()

    def __str__(self):
        pegged_bids = '\n'.join(
            'Order ID: {}, Volume: {}'.format(oid, vol) for (oid, vol) in self.pegged_bids.items()
        )
        pegged_asks = '\n'.join(
            'Order ID: {}, Volume: {}'.format(oid, vol) for (oid, vol) in self.pegged_asks.items()
        )
        return """Spread: {} - {}
Peg Price: ${}
  Bids:
{}
  Asks:
{}
  Pegged Bids:
{}
  Pegged Asks:
{}
""".format(self.bid, self.ask, self.peg_price, self.bids, self.asks, pegged_bids, pegged_asks)

    # fill `volume`'s worth of pegged orders
    # if `fill_bids` is true, bids are filled. else asks are filled
    def fill_pegged_orders(self, volume, fill_bids):
        volume_to_fill = volume
        fulfilling_orders = []
        order_queue = self.pegged_bids if fill_bids else self.pegged_asks
        while volume_to_fill > 0 and len(order_queue) > 0:
            (order_id, order_volume) = next(iter(order_queue.items()))
            if order_volume > volume_to_fill:
                order_queue[order_id] = order_volume - volume_to_fill
                fulfilling_orders.append( (order_id, volume_to_fill) )
                volume_to_fill = 0
            else:
                del order_queue[order_id]
                fulfilling_orders.append( (order_id, order_volume) )
                volume_to_fill -= order_volume
        return fulfilling_orders

    def cancel_order(self, order_id, price, volume, buy_sell_indicator, midpoint_peg):
        '''
        Cancel all or part of an order. Volume refers to the desired remaining shares to be executed: if it is 0, the order is
        fully cancelled, otherwise an order of volume volume remains.
        '''

        if midpoint_peg:
            return self.cancel_pegged_order(order_id, volume, buy_sell_indicator)
        else:
            return super().cancel_order(order_id, price, volume, buy_sell_indicator)
    
    def cancel_pegged_order(self, order_id, volume, buy_sell_indicator):
        order_queue = self.pegged_bids if buy_sell_indicator == b'B' else self.pegged_asks
        if order_id not in order_queue:
            log.debug('No order in the book to cancel, cancel ignored.')
            return [], None
        
        if volume == 0:
            amount_canceled = order_queue[order_id]
            del order_queue[order_id]
        elif order_queue[order_id] > volume:
            amount_canceled = order_queue[order_id] - volume
            order_queue[order_id] = volume
        else:
            amount_canceled = 0
        return [(order_id, amount_canceled)], None

    def enter_buy(self, order_id, price, volume, enter_into_book, midpoint_peg):
        '''
        Enter a limit order to buy at price price: first, try and fulfill as much as possible, then enter if required
        '''
        order_crosses = []
        entered_order = None
        bbo_update = None

        if midpoint_peg and not self.peg_price:
            log.warn('pegged order entered before peg price is set, dropping order')
            return ([], (), None)
        # if this order is pegged and its start price isn't aggressive, just drop it
        if midpoint_peg and price < self.peg_price: 
            return ([], (), None)

        # if this order is pegged and it is aggressive enough, use peg point as the price
        if midpoint_peg:
            effective_price = self.peg_price
        # otherwise it's a normal order, just use its normal price
        else:
            effective_price = price

        volume_to_fill = volume
        # edge case: we need to check pegged orders even when there are no normal orders
        if self.peg_price and len(self.asks) == 0 and effective_price >= self.peg_price:
            fulfilling_orders = self.fill_pegged_orders(volume_to_fill, False)
            for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                order_crosses.append(((order_id, fulfilling_order_id), self.peg_price, cross_volume))
                volume_to_fill -= cross_volume

        peg_checked = False
        for price_q in self.asks.ascending_items():
            # if we've already checked all more agressive limit orders, check pegged orders
            if not peg_checked and self.peg_price and self.peg_price < price_q.price and effective_price >= self.peg_price:
                fulfilling_orders = self.fill_pegged_orders(volume_to_fill, False)
                for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                    order_crosses.append(((order_id, fulfilling_order_id), self.peg_price, cross_volume))
                    volume_to_fill -= cross_volume
                peg_checked = True

            if price_q.price > effective_price:
                break
            
            (filled, fulfilling_orders) = price_q.fill_order(volume_to_fill)

            for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                order_crosses.append(((order_id, fulfilling_order_id), price_q.price, cross_volume))
                volume_to_fill -= cross_volume
            
            if price_q.interest==0:
                self.asks.remove(price_q.price)
                new_bbo = self.update_ask()
                if new_bbo:
                    bbo_update = new_bbo

            if volume_to_fill <= 0:
                break                    

        if volume_to_fill > 0 and enter_into_book:
            if midpoint_peg:
                self.pegged_bids[order_id] = volume_to_fill
            else:
                self.bids[price].add_order(order_id, volume_to_fill)
                new_bbo = self.update_bid()
                if new_bbo:
                    bbo_update = new_bbo
            entered_order = (order_id, effective_price, volume_to_fill)

        return (order_crosses, entered_order, bbo_update) 

    def enter_sell(self, order_id, price, volume, enter_into_book, midpoint_peg):
        '''
        Enter a limit order to sell at price price: first, try and fulfill as much as possible, then enter if required
        '''
        order_crosses = []
        entered_order = None
        bbo_update = None

        if midpoint_peg and not self.peg_price:
            log.warn('pegged order entered before peg price is set, dropping order')
            return ([], (), None)
        # if this order is pegged and its start price isn't aggressive, just drop it
        if midpoint_peg and price > self.peg_price: 
            return ([], (), None)

        # if this order is pegged and it is aggressive enough, use peg point as the price
        if midpoint_peg:
            effective_price = self.peg_price
        # otherwise it's a normal order, just use its normal price
        else:
            effective_price = price

        volume_to_fill = volume
        # edge case: we need to check pegged orders even when there are no normal orders
        if self.peg_price and len(self.bids) == 0 and effective_price <= self.peg_price:
            fulfilling_orders = self.fill_pegged_orders(volume_to_fill, True)
            for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                order_crosses.append(((order_id, fulfilling_order_id), self.peg_price, cross_volume))
                volume_to_fill -= cross_volume

        peg_checked = False
        for price_q in self.bids.ascending_items():
            # if we've already checked all more agressive limit orders,
            # check pegged orders. use flag so pegs are only checked once
            if not peg_checked and self.peg_price and self.peg_price > price_q.price and effective_price <= self.peg_price:
                fulfilling_orders = self.fill_pegged_orders(volume_to_fill, True)
                for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                    order_crosses.append(((order_id, fulfilling_order_id), self.peg_price, cross_volume))
                    volume_to_fill -= cross_volume
                peg_checked = True

            if price_q.price < effective_price:
                break
            
            (filled, fulfilling_orders) = price_q.fill_order(volume_to_fill)

            for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                order_crosses.append(((order_id, fulfilling_order_id), price_q.price, cross_volume))
                volume_to_fill -= cross_volume
            
            if price_q.interest==0:
                self.bids.remove(price_q.price)
                new_bbo = self.update_bid()
                if new_bbo:
                    bbo_update = new_bbo

            if volume_to_fill <= 0:
                break                    

        if volume_to_fill > 0 and enter_into_book:
            if midpoint_peg:
                self.pegged_asks[order_id] = volume_to_fill
            else:
                self.asks[price].add_order(order_id, volume_to_fill)
                new_bbo = self.update_ask()
                if new_bbo:
                    bbo_update = new_bbo
            entered_order = (order_id, effective_price, volume_to_fill)

        return (order_crosses, entered_order, bbo_update) 
    
    # check whether any pegged bids have crossed with non-pegged asks
    # and return crosses/new bbo if they have
    def check_ask_peg_cross(self):
        if not len(self.pegged_bids) or not len(self.asks):
            return ([], None)

        order_crosses = []
        for price_q in self.asks.ascending_items():
            if price_q.price > self.peg_price:
                break

            for (pegged_order_id, pegged_order_volume) in list(self.pegged_bids.items()):
                (filled, fulfilling_orders) = price_q.fill_order(pegged_order_volume)
                for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                    order_crosses.append(((pegged_order_id, fulfilling_order_id), price_q.price, cross_volume))

                self.pegged_bids[pegged_order_id] -= filled
                # if filling this order used all the peg's volume, remove the peg
                if self.pegged_bids[pegged_order_id] == 0:
                    del self.pegged_bids[pegged_order_id]
                
            if price_q.interest == 0:
                self.asks.remove(price_q.price)

        bbo_update = None
        if len(order_crosses):
            bbo_update = self.update_ask()
        return (order_crosses, bbo_update)

    # check whether any pegged asks have crossed with non-pegged bids
    # and return crosses/new bbo if they have
    def check_bid_peg_cross(self):
        if not len(self.pegged_asks) or not len(self.bids):
            return ([], None)

        order_crosses = []
        for price_q in self.bids.ascending_items():
            if price_q.price < self.peg_price:
                break

            for (pegged_order_id, pegged_order_volume) in list(self.pegged_asks.items()):
                (filled, fulfilling_orders) = price_q.fill_order(pegged_order_volume)
                for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                    order_crosses.append(((pegged_order_id, fulfilling_order_id), price_q.price, cross_volume))

                self.pegged_asks[pegged_order_id] -= filled
                # if filling this order used all the peg's volume, remove the peg
                if self.pegged_asks[pegged_order_id] == 0:
                    del self.pegged_asks[pegged_order_id]

            if price_q.interest == 0:
                self.bids.remove(price_q.price)

        bbo_update = None
        if len(order_crosses):
            bbo_update = self.update_bid()
        return (order_crosses, bbo_update)

    # called externally:
    # change the peg price for midpoint pegged orders.
    # possible return a list of crossed orders and/or a new bbo
    def update_peg_price(self, new_price):
        old_price = self.peg_price
        self.peg_price = new_price
        if new_price is None:
            return ([], None)
        elif old_price is None:
            # if we go from no peg to having a peg, we need to check for both bid and ask crosses
            ask_crosses, ask_bbo = self.check_ask_peg_cross()
            bid_crosses, bid_bbo = self.check_bid_peg_cross()
            crosses = ask_crosses + bid_crosses
            if bid_bbo is not None:
                return (crosses, bid_bbo)
            else:
                return (crosses, ask_bbo)
        elif new_price > old_price:
            return self.check_ask_peg_cross()
        else:
            return self.check_bid_peg_cross()
