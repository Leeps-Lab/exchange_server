
class SimpleOrderBook:
	def __init__(
			min_price = 0.0, 
			max = 100.0, 
			decrement = 0.01,
			order_filled_callback = lambda (order_id, volume): None ):

		self.min_price = min_price
		self.max_price = max_price 
		self.decrement = decrement

		self.bid = min_price
		self.ask = max_price

		self.orders = dict()
		self.order_array = [ BookPriceQ() for price in range(self.min_price, self.max_price, self.decrement)]

	def enter_limit_buy(id, price, volume):
	"""
	Enter a limit order to buy at price price
	"""
		if price >= self.ask:
			# fulfill as much of the order as possible, starting from self.ask

			# add open buy order with remaining volume at price price


	def enter_limit_sell(id, price, volume):
	"""
	Enter a limit order to sell at price price
	"""
		if price <= self.bid:
			# fulfill as much of the order as possible, starting from self.bid

			# add open sell order with remaining volume at price price




class BookPriceQ:
	def __init__():
		self.interest = 0 	#sum of interest at this price
		self.order_q = OrderedDict()
	
	def add_order(order_id, volume):
		self.interest += volume
		self.order_q[order_id] = volume

	def cancel_order(order_id):
		self.interest -= self.order_q[order_id]
		del self.order_q[order_id]

	def fill_order(volume):
		'''
		For a given order volume to fill, dequeue's the oldest orders 
		at this price point to be used to fill the order. 

		Returns a tuple giving the volume filled at this price, and a list of (order_id, order_volume) pairs giving the order volume amount filled from each order in the book.
		'''
		volume_to_fill = volume
		fulfilling_orders = []

		while volume_to_fill > 0 and len(self.order_q)>0:
			next_order_id = next(iter(self.order_q))
			next_order_volume = self.order_q[next_order_id]

			if next_order_volume > volume_to_fill:
				self.order_q[next_order_id] = next_order_volume -volume_to_fill
				fulfilling_orders.add((next_order_id, volume_to_fill))
				volume_to_fill = 0				
			else:
				fulfilling_orders.append(self.order_q.popitem())

		volume_fulfilled = volume - volume_to_fill
		self.interest -= volume_fulfilled

		return (volume_fulfilled, 
				fulfilling_orders)