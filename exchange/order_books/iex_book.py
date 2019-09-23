
import sys
from collections import OrderedDict
import logging as log
from .book_price_q import IEXBookPriceQ
from .list_elements import IEXAskList, IEXBidList
import itertools

MIN_BID = 0
MAX_ASK = 2147483647

class IEXBook:
    def __init__(self):
        self.bid = MIN_BID
        self.ask = MAX_ASK
        self.bids = IEXBidList()
        self.asks = IEXAskList()
        self.bounds = (MIN_BID, MAX_ASK)
        self.mpegs = {}
        self.nbbo_midpoint = 10

    def __str__(self):
        return """  
  
  Spread: {} - {}

  Bids:
{}

  Asks:
{}
""".format(self.bid, self.ask, self.bids, self.asks)

    def reset_book(self):						#jason
        log.info('Clearing All Entries from Order Book')
        self.bid = MIN_BID
        self.ask = MAX_ASK
        for id in list(self.asks.index):		#force as list because can't interate dict and delete keys at same time
                    self.asks.remove(id)
        for id in list(self.bids.index):
                    self.bids.remove(id)


    def calc_limpeg_price(self, price, buy_sell_indicator):
        """
        calculates the effective price for
        limit pegged orders
        """
        constant = 1 if buy_sell_indicator == b'B' else -1
        nbbo = self.nbbo_midpoint
        effective_price = price if constant * price < constant * nbbo else nbbo
        return effective_price
            

    def cancel_from_nbbo(self, id, price, buy_sell_indicator, lit):
        orders = self.bids if buy_sell_indicator == b'B' else self.asks
        effective_price = price
        if price not in self.bounds:
            # order is a limit midpoint peg
            effective_price = self.calc_limpeg_price(price, buy_sell_indicator)
        orders[(effective_price, lit)].cancel_order(id)
        if orders[(effective_price, lit)].interest == 0:
            orders.remove((effective_price, lit))
        if effective_price == self.bid:
            self.update_bid()
        elif effective_price == self.ask:
            self.update_ask()
        

    def cancel_order(self, id, price, volume, buy_sell_indicator, lit, midpoint_peg):
        '''
        Cancel all or part of an order. Volume refers to the desired remaining shares to be executed: if it is 0, the order is
        fully cancelled, otherwise an order of volume volume remains.
        '''
        orders = self.bids if buy_sell_indicator == b'B' else self.asks
        effective_price = price
        if midpoint_peg and price not in self.bounds:
            # order is a limit midpoint peg
            effective_price = self.calc_limpeg_price(price, buy_sell_indicator)
        if (effective_price, lit) not in orders or id not in orders[(effective_price, lit)].order_q:
            print('No order in the book to cancel, cancel ignored.')
            return []
        else:
            amount_canceled=0
            current_volume=orders[(effective_price, lit)].order_q[id]
            if volume==0: 										#fully cancel
                orders[(effective_price, lit)].cancel_order(id)
                if midpoint_peg:
                    del self.mpegs[id]
                amount_canceled = current_volume
                if orders[(effective_price, lit)].interest == 0:
                    orders.remove((effective_price, lit))
            elif current_volume >= volume:
                orders[(effective_price, lit)].reduce_order(id, volume)		
                amount_canceled = current_volume - volume
            else:
                amount_canceled = 0

            if effective_price == self.bid:
                self.update_bid()
            elif effective_price == self.ask:
                self.update_ask()

            return [(id, amount_canceled)]

    def update_bid(self):
        if self.bids.start is None:
            self.bid = MIN_BID 
        else:
            self.bid = self.bids.start.data.price
        #while self.price_q[self.bid].interest == 0 and self.bid > self.min_price:
        #	self.bid -= self.decrement

    def update_ask(self):
        if self.asks.start is None:
            self.ask = MAX_ASK
        else:
            self.ask = self.asks.start.data.price
        #while self.price_q[self.ask].interest == 0 and self.ask < self.max_price:
        #	self.ask += self.decrement		

    def enter_buy(self, id, price, volume, lit, enter_into_book, midpoint_peg=False):
        '''
        Enter a limit order to buy at price price: first, try and fulfill as much as possible, then enter a
        '''
        order_crosses=[]
        entered_order = None
        effective_price = price
        if midpoint_peg: 
            nbbo = self.nbbo_midpoint
            effective_price = price if price < nbbo else nbbo
        volume_to_fill = volume
        if effective_price >= self.ask:
            for price_q in self.asks.ascending_items():
                if price_q.price > effective_price:
                    break
                
                (filled, fulfilling_orders, drained_orders) = price_q.fill_order(volume_to_fill)
                if drained_orders:
                    in_mpegs = map(lambda x: x if x in self.mpegs else None, drained_orders)
                    mpegs = list(filter(lambda x: x is True, in_mpegs))
                    if mpegs:
                        for mpeg in mpegs:
                            assert self.mpegs[mpeg]
                            del self.mpegs[mpeg]

                for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                    order_crosses.append(((id, fulfilling_order_id), price_q.price, cross_volume))
                    volume_to_fill -= cross_volume
                
                if price_q.interest==0:
                    self.asks.remove((effective_price, price_q.lit))
                    self.update_ask()

                if volume_to_fill <= 0:
                    break					

        if volume_to_fill > 0 and enter_into_book:
            self.bids[(effective_price, lit)].add_order(id, volume_to_fill)
            self.update_bid()
            entered_order = (id, price, volume_to_fill)
            if midpoint_peg and id not in self.mpegs:
                self.mpegs[id] = price
        return (order_crosses, entered_order) 

    def enter_sell(self, id, price, volume, lit, enter_into_book, midpoint_peg=True):
        '''
        Enter a limit order to sell at price price: first try and fulfill as much as possible, then enter the
        remaining as a limit sell
        '''
        order_crosses=[]
        entered_order = None
        effective_price = price
        if midpoint_peg: 
            nbbo = self.nbbo_midpoint 
            effective_price = price if price > nbbo else nbbo
        volume_to_fill = volume
        if effective_price <= self.bid:
            for price_q in self.bids.ascending_items():
                if price_q.price < effective_price:
                    break
                
                (filled, fulfilling_orders, drained_orders) = price_q.fill_order(volume_to_fill)
                if drained_orders:
                    in_mpegs = map(lambda x: x if x in self.mpegs else None, drained_orders)
                    mpegs = list(filter(lambda x: x is True, in_mpegs))
                    if mpegs:
                        for mpeg in mpegs:
                            assert self.mpegs[mpeg]
                            del self.mpegs[mpeg]
                for (fulfilling_order_id, cross_volume) in fulfilling_orders:
                    order_crosses.append(((id, fulfilling_order_id), price_q.price, cross_volume))
                    volume_to_fill -= cross_volume
                
                if price_q.interest==0:
                    self.bids.remove((price_q.price, price_q.lit))
                    self.update_bid()

                if volume_to_fill <= 0:
                    break					
            
        if volume_to_fill > 0 and enter_into_book:
            self.asks[(effective_price, lit)].add_order(id, volume_to_fill)
            self.update_ask()
            entered_order = (id, price, volume_to_fill)
            if midpoint_peg and id not in self.mpegs:
                self.mpegs[id] = price
        return (order_crosses, entered_order) 
    
    def enter_from_nbbo(self, id, price, volume, lit, buy_sell_indicator, midpoint_peg=True):
        if buy_sell_indicator == b'B':
            order_crosses, entered_order = self.enter_buy(id, price, volume, lit, True, midpoint_peg=True)
        elif buy_sell_indicator == b'S':
            order_crosses, entered_order = self.enter_sell(id, price, volume, lit, True, midpoint_peg=True)
        else:
            pass
        

    def nbbo_update(self, new_nbbo):
        def update_rule(price, limit, buy_sell_indicator):
            new_price = new_nbbo
            aggressive = False
            constant = 1 if buy_sell_indicator == b'B' else -1
            if constant * limit < constant * new_nbbo:
                new_price = limit
            if constant * price < constant * new_nbbo:
                aggressive = True
            return (new_price, aggressive)

        cancels_bus = []
        enter_aggresive_bus = []
        enter_passive_bus = []
        for bpq in itertools.chain(self.bids.descending_items(), self.asks.descending_items()):
             mpegs = [(ix, vol) for ix, vol in bpq.order_q.items() if ix in self.mpegs]
             if mpegs:
                 for pair in mpegs:
                    mpeg_id, volume = pair
                    limit = self.mpegs[mpeg_id]
                    new_price, aggressive = update_rule(bpq.price, limit, bpq.side)
                    if new_price != bpq.price:
                        cancel_args = (mpeg_id, bpq.price, bpq.side, bpq.lit)
                        cancels_bus.append(cancel_args)
                        enter_args = (mpeg_id, new_price, volume, bpq.lit, bpq.side)
                        if aggressive:
                            enter_aggresive_bus.append(enter_args)
                        else:
                            enter_passive_bus.append(enter_args)

        for args in cancels_bus:
            self.cancel_from_nbbo(*args)
        self.nbbo_midpoint = new_nbbo    
        for l in enter_passive_bus, enter_aggresive_bus:
            for args in l:
                self.enter_from_nbbo(*args)
        


def test():
    book = IEXBook()
    (crossed_orders, entered_order) =  book.enter_buy(1, 10, 2, True, True, midpoint_peg=False)
    assert len(crossed_orders)==0
    assert entered_order==(1,10,2)
    assert book.bid==10
    print(book)

    (crossed_orders, entered_order)  = book.enter_buy(2, 11, 3, True, True, midpoint_peg=False)
    assert len(crossed_orders)==0
    assert entered_order==(2,11,3)
    assert book.bid==11
    print(book)

    (crossed_orders, entered_order) = book.enter_sell(3, 8, 10, True, True, midpoint_peg=True)
    assert len(crossed_orders)==2
    assert crossed_orders[0]==((3, 2), 11, 3)
    assert crossed_orders[1]==((3, 1), 10, 2)
    assert entered_order==(3,8,5)
    print(book)
    (crossed_orders, entered_order) = book.enter_sell(4, MIN_BID, 10, True, True, midpoint_peg=True)
    print(book)
    (crossed_orders, entered_order) = book.enter_sell(5, MIN_BID, 5, True, True, midpoint_peg=True)
    print(book)
    (crossed_orders, entered_order) = book.enter_buy(6, MAX_ASK, 5, True, True, midpoint_peg=False)
    print(book)
    (crossed_orders, entered_order) =book.enter_buy(7, MAX_ASK, 5, True, True, midpoint_peg=True)
    print(book)
    for nbbo in (14, 8, 6, 9, 4):
        book.nbbo_update(nbbo)
        print(book)  
    (crossed_orders, entered_order) =book.enter_buy(8, 20, 20, False, True, midpoint_peg=True)
    print(book)
    (crossed_orders, entered_order) =book.enter_buy(9, 18, 20, True, True, midpoint_peg=True)
    print(book)
    for nbbo in (15, 18, 24, 10):
        book.nbbo_update(nbbo)
        print(book)


    #should sell to both of the entered buy orders

if __name__ == '__main__':
    test()
