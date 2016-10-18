from collections import OrderedDict
import logging as log

class SimpleOrderBook:
	def __init__(self,
			min_price = 0, 
			max_price = 100):

		self.min_price = min_price
		self.max_price = max_price 
		self.decrement = 1
		self.bid = min_price
		self.ask = max_price
		self.orders = dict()
		self.price_q = [ BookPriceQ() for price in range(self.min_price, self.max_price+1, self.decrement)]
	
	def __str__(self):
		bids = '\n'.join(['${} : {}'.format(price, str(price_qp)) for (price, price_qp) in enumerate(self.price_q) if price_qp.interest>0 and price<=self.bid])
		asks = '\n'.join(['${} : {}'.format(price, str(price_qp)) for (price, price_qp) in enumerate(self.price_q) if price_qp.interest>0 and price>=self.ask])

		return """Bids:
{}

Asks:
{}""".format(bids, asks)

	def cancel_order(self, id, price, volume):
		self.price_q[price].cancel_order(id)
		#TODO - check for change in bin/ask spread


	def enter_limit_buy(self, id, price, volume):
		'''
		Enter a limit order to buy at price price: first, try and fulfill as much as possible, then enter a
		'''
		order_crosses=[]
		entered_order = None
		volume_to_fill = volume
		if price >= self.ask:
			while volume_to_fill > 0 and self.ask <= price:
				fulfilling_orders = self.price_q[self.ask].fill_order(volume_to_fill)
				for (fulfilling_order_id, cross_volume) in fulfilling_orders:
					order_crosses.append(((id, fulfilling_order_id), self.ask, cross_volume))
					volume_to_fill -= cross_volume
				while self.price_q[self.ask].interest == 0 and self.ask < self.max_price:
					self.ask += self.decrement				
		if volume_to_fill > 0:
			self.price_q[price].add_order(id, volume_to_fill)
			if price > self.bid:
				self.bid = price
			entered_order = (id, price, volume_to_fill)
		return (order_crosses, entered_order) 

	def enter_limit_sell(self, id, price, volume):
		'''
		Enter a limit order to sell at price price: first try and fulfill as much as possible, then enter the
		remaining as a limit sell
		'''
		order_crosses=[]
		entered_order = None
		volume_to_fill = volume
		if price <= self.bid:
			while volume_to_fill > 0 and self.bid >= price:
				log.debug('enter_limit_sell: volume_to_fill:%s, bid:%s, price:%s ', volume_to_fill, self.bid, price)
				fulfilling_orders = self.price_q[self.bid].fill_order(volume_to_fill)
				for (fulfilling_order_id, cross_volume) in fulfilling_orders:
					order_crosses.append(((id,fulfilling_order_id), self.bid, cross_volume))
					volume_to_fill -= cross_volume
				while self.price_q[self.bid].interest == 0 and self.bid > self.min_price:
					self.bid -= self.decrement				
		if volume_to_fill > 0:
			self.price_q[price].add_order(id, volume_to_fill)
			if price < self.ask:
				self.ask = price
			entered_order = (id, price, volume_to_fill)
		return (order_crosses, entered_order) 

class BookPriceQ:
	def __init__(self):
		self.interest = 0 	#sum of interest at this price
		self.order_q = OrderedDict()
	
	def __str__(self):
		return 'Interest: {}, Orders: {}'.format(self.interest, ','.join(['{}: {}'.format(id, volume) for (id, volume) in self.order_q.items()]))

	def add_order(self, order_id, volume):
		self.interest += volume
		self.order_q[order_id] = volume

	def cancel_order(self, order_id):
		self.interest -= self.order_q[order_id]
		del self.order_q[order_id]

	def fill_order(self, volume):
		'''
		For a given order volume to fill, dequeue's the oldest orders 
		at this price point to be used to fill the order. 

		Returns a tuple giving the volume filled at this price, and a list of (order_id, order_volume) pairs giving the order volume amount filled from each order in the book.
		'''
		volume_to_fill = volume
		fulfilling_orders = []
		while volume_to_fill > 0 and len(self.order_q)>0:
			log.debug('  fill_order: volume_to_fill = %s', volume_to_fill)
			next_order_id = next(iter(self.order_q))
			next_order_volume = self.order_q[next_order_id]
			if next_order_volume > volume_to_fill:
				assert self.order_q[next_order_id] ==next_order_volume
				self.order_q[next_order_id] = next_order_volume-volume_to_fill
				fulfilling_orders.append((next_order_id, volume_to_fill))
				self.interest -= volume_to_fill	
				volume_to_fill = 0			
			else:
				volume_to_fill -= next_order_volume
				fulfilling_orders.append(self.order_q.popitem(last=False))
				self.interest -= next_order_volume
		return fulfilling_orders

def test():
	book = SimpleOrderBook()
	(crossed_orders, entered_order) =  book.enter_limit_buy(1, 10, 2)
	print(crossed_orders, entered_order)
	assert len(crossed_orders)==0
	assert entered_order==(1,10,2)
	assert book.bid==10
	assert book.ask==book.max_price

	(crossed_orders, entered_order)  = book.enter_limit_buy(2, 11, 3)
	print(crossed_orders, entered_order)
	assert len(crossed_orders)==0
	assert entered_order==(2,11,3)
	assert book.bid==11
	assert book.ask==book.max_price

	(crossed_orders, entered_order) = book.enter_limit_sell(3, 8, 10)
	print(crossed_orders, entered_order)
	assert len(crossed_orders)==2
	assert crossed_orders[0]==((2, 3), 11, 3)
	assert crossed_orders[1]==((1, 3), 10, 2)
	assert entered_order==(3,8,5)
	assert book.bid==book.min_price
	assert book.ask==8

	#should sell to both of the entered buy orders

if __name__ == '__main__':
	test()

