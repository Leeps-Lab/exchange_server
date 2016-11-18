from exchange.order_books.book_price_q import BookPriceQ
from exchange.order_books.list_elements import SortedIndexedDefaultList
import heapq

MIN_BID = 0
MAX_ASK = 2000000000


class FBABook:
	def __init__(self):
		self.bids = SortedIndexedDefaultList(index_func = lambda bq: bq.price, 
							initializer = lambda p: BookPriceQ(p),
							index_multiplier = -1)
		self.asks = SortedIndexedDefaultList(index_func = lambda bq: bq.price, 
							initializer = lambda p: BookPriceQ(p))

	def __str__(self):
		return """  Spread: {} - {}
  Bids:
{}

  Asks:
{}""".format(self.bid, self.ask, self.bids, self.asks)


	def cancel_order(self, id, price, volume, buy_sell_indicator):
		'''
		Cancel all or part of an order. Volume refers to the desired remaining shares to be executed: if it is 0, the order is
		fully cancelled, otherwise an order of volume volume remains.
		'''
		orders = self.bids if buy_sell_indicator == b'B' else self.asks
		
		if price not in orders or id not in orders[price].order_q:
			log.debug('No order in the book to cancel, cancel ignored.')
			return []
		else:
			amount_canceled=0
			current_volume=orders[price].order_q[id]
			if volume==0: 										#fully cancel
				orders[price].cancel_order(id)
				amount_canceled = current_volume
				if orders[price].interest == 0:
					orders.remove(price)
			elif volume < current_volume:
				orders[price].reduce_order(id, volume)		
				amount_canceled = current_volume - volume
			else:
				amount_canceled = 0

			return [(id, amount_canceled)]

	def enter_buy(self, id, price, volume, enter_into_book = True):
		'''
		Enter a limit order to buy at price price: do NOT try and match
		'''
		if enter_into_book:
			self.bids[price].add_order(id, volume_to_fill)
			entered_order = (id, price, volume_to_fill)
			return ([], entered_order) 

	def enter_sell(self, id, price, volume, enter_into_book):
		'''
		Enter a limit order to sell at price price: do NOT try and match
		'''
				'''
		Enter a limit order to buy at price price: do NOT try and match
		'''
		if enter_into_book:
			self.asks[price].add_order(id, volume_to_fill)
			entered_order = (id, price, volume_to_fill)
			return ([], entered_order) 


	def batch_process(self):
		log.debug('Running batch auction..')
		asks_volume = sum([price_book.data.interest for price_book in self.asks.ascending_items()])
		all_orders_descending = heapq.merge(
			self.asks.descending_items(), 
			self.bids.ascending_items(), 
			key: lambda node: node.data.price, 
			reverse=True)
		
		orders_volume = 0
		clearing_price = None

		log.debug('Calculating clearing price..')
		for n in all_orders_descending:
			if orders_volume >= asks_volume:
				break
			else:
				orders_volume += n.data.interest
				clearing_price = n.data.price
		log.debug('Clearing price: {}', clearing_price)

		matches = []
		ask_it = self.asks.ascending_items()
		ask_node = ask_it.next()
		ask_price = ask_node.data.price

		#iterate over bids starting with highest
		for bid_node in self.bids.ascending_items():
			bid_price = bid_node.data.price
			if bid_price<clearing_price or ask_price>clearing_price:
				break
			else:
				for (bid_id, volume) in bid_node.data.order_q.iteritems():
					volume_filled = 0
					while volume_filled < volume and ask_price <= clearing_price:
						(filled, fulfilling_orders) = ask_node.data.fill_order(volume)
						volume_filled += filled
						matches.extend([((bid_id, ask_id), clearing_price, volume) for (ask_id, volume) in fulfilling_orders])
						if volume_filled < volume:
							ask_node = ask_it.next()
							ask_price = ask_node.data.price
					#update bid in book
					if volume_filled==volume:
						bid_node.data.cancel_order(bid_id)
					elif volume_filled >0:
						bid_node.reduce_order(order_id, volume - volume_filled)
		return matches



