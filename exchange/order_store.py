import logging as log


class OrderStore:
	'''
	An order store keeps tracks of orders submitted to the exchange and their
	status.
	'''

	def __init__(self):
		self.orders = {}

	def store_order(self, id, message, executed_quantity = 0):
		'''
		Called to create a new order store entry, either with an EnterOrder message, or a replace order message that creates a new order.

		Returns true if successful in storing it; false if unsuccesful because the order token is already used.
		'''
		if id in self.orders:
			log.info('Ignoring store_order command: id %s already in the order store', id)
			return False
		else:
			self.orders[id] = OrderStoreEntry(message, executed_quantity)
			return self.orders[id]

	def add_to_order(self, id, message):
		'''
		Called to add a message an existing order.
		'''
		if id not in self.orders:
			log.error('Unknown existing order %s', id)
			return False
		else:
			self.orders[id].add_to_order(message)

	def execute_quantity(self, id, quantity):
		self.orders[id].executed_quantity += quantity

class OrderStoreEntry:
	def __init__(self, original_message, executed_quantity):
		self.history = []
		self.executed_quantity = executed_quantity
		self.original_message = original_message

	def add_to_order(self, message):
		self.history.append(message)

