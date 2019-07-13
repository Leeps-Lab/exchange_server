from exchange.order_books.book_price_q import BookPriceQ   
from random import randint
from itertools import count
import logging as log

class FBABookPriceQ(BookPriceQ):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_batch_number = 0
        self.batch_marker = 0
    
    def add_order(self, order_id, volume, order_batch_number):
        self.interest += volume
        self.order_q[order_id] = (volume, order_batch_number)
        if self.current_batch_number == order_batch_number:
            batch_start_index = self.batch_marker
            batch_end_index = len(self.order_q) - 1
            random_index = randint(batch_start_index, batch_end_index)
            rest_of_batch = list(self.order_q.keys())[random_index : -1]
            if rest_of_batch:
                for o in rest_of_batch:
                    self.order_q.move_to_end(o)
        else:
            self.order_q[order_id] = (volume, order_batch_number)
            self.batch_marker = len(self.order_q) - 1
            self.current_batch_number = order_batch_number
        
    def cancel_order(self, order_id, live_batch_number):
        volume, order_batch_number = self.order_q[order_id]
        self.interest -= volume
        del self.order_q[order_id]
        if order_batch_number != live_batch_number:
            self.batch_marker -= 1      
    
    def reduce_order(self, order_id, new_volume):
        volume, _ = self.order_q[order_id]
        assert new_volume <= volume
        self.order_q[order_id] = (new_volume, _)
        self.interest -= (volume - new_volume)

    def fill_order(self, volume):
        volume_to_fill = volume
        fulfilling_orders = []
        while volume_to_fill > 0 and len(self.order_q)>0:
            next_order_id = next(iter(self.order_q))
            next_order_volume, _ = self.order_q[next_order_id]
            if next_order_volume > volume_to_fill:
                assert self.order_q[next_order_id][0] == next_order_volume
                self.order_q[next_order_id] = (next_order_volume - volume_to_fill, _)
                fulfilling_orders.append((next_order_id, volume_to_fill))
                self.interest -= volume_to_fill	
                volume_to_fill = 0			
            else:
                volume_to_fill -= next_order_volume
                fulfilling_orders.append(self.order_q.popitem(last=False))
                self.interest -= next_order_volume
        return (volume - volume_to_fill, fulfilling_orders)
