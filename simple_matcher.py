


class BidAskQueue(object):
""" Represents a queue of bids / asks for a given price point.
	For each limit order, stores (quantity, order_id)
	Keeps track of total demand of the list
"""
	def __init__(price):
		self.q = []
		self.price=price
		self.total_qty = 0

	def add(order):
		






class SimpleCLOB():
	def __init__(tick_size=0.01, min=0, max=1000):
		self.bids = []
		self.asks = []

	def match_order(order):
