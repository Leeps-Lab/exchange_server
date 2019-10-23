import unittest
from iex_book import IEXBook

class TestIEXBook(unittest.TestCase):

    def test_unpegged_orders_buy(self):
        book = IEXBook()

        # enter buy order at $10 for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(1, 10, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [])

        # enter sell order at $10 for 1 unit
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(2, 10, 1, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((2, 1), 10, 1)])

        # enter sell order at $8 for 1 unit
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(3, 8, 1, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((3, 1), 10, 1)])

        # book should be empty
        self.assertEqual(len(book.bids), 0)
        self.assertEqual(len(book.asks), 0)

    def test_unpegged_orders_sell(self):
        book = IEXBook()

        # enter sell order at $10 for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(1, 10, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [])

        # enter buy order at $10 for 1 unit
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(2, 10, 1, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((2, 1), 10, 1)])

        # enter buy order at $11 for 1 unit
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(3, 11, 1, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((3, 1), 10, 1)])

        # book should be empty
        self.assertEqual(len(book.bids), 0)
        self.assertEqual(len(book.asks), 0)
    
    def test_peg_crossing_buy(self):
        book = IEXBook()
        book.update_peg_price(9)

        # enter buy order at $10 for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(1, 10, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [])

        # enter nonaggressive pegged sell order
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(2, 10, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])
        self.assertEqual(len(book.pegged_asks), 0)

        # enter aggressive pegged sell order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(3, 2, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [((3, 1), 10, 1)])

        # move peg price past remaining order
        book.update_peg_price(11)

        # enter aggressive pegged sell order with volume 1, should not cross
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(4, 2, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])

        # should be one unpegged bid and one pegged ask
        self.assertEqual(len(book.bids), 1)
        self.assertEqual(book.bids[10].interest, 1)
        self.assertEqual(len(book.pegged_asks), 1)
        self.assertEqual(book.pegged_asks[4], 1)

    def test_peg_crossing_sell(self):
        book = IEXBook()
        book.update_peg_price(11)

        # enter sell order at $10 for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(1, 10, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [])

        # enter nonaggressive pegged buy order
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(2, 7, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])
        self.assertEqual(len(book.pegged_bids), 0)

        # enter aggressive pegged buy order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(3, 12, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [((3, 1), 10, 1)])

        # move peg price past remaining order
        book.update_peg_price(8)

        # enter aggressive pegged buy order with volume 1, should not cross
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(4, 12, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])

        # should be one unpegged ask and one pegged bid
        self.assertEqual(len(book.asks), 1)
        self.assertEqual(book.asks[10].interest, 1)
        self.assertEqual(len(book.pegged_bids), 1)
        self.assertEqual(book.pegged_bids[4], 1)
    
    def test_peg_repricing_crosses_buy(self):
        book = IEXBook()
        book.update_peg_price(15)

        # enter buy order at $10 for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(1, 10, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [])

        # enter aggressive pegged sell order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(2, 12, 2, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])

        # move peg point so pegged order crosses
        (crossed_orders, new_bbo) = book.update_peg_price(9)
        self.assertEqual(crossed_orders, [((2, 1), 10, 2)])

        # book should be empty
        self.assertEqual(len(book.bids), 0)
        self.assertEqual(len(book.asks), 0)
        self.assertEqual(len(book.pegged_bids), 0)
        self.assertEqual(len(book.pegged_asks), 0)

    def test_peg_repricing_crosses_sell(self):
        book = IEXBook()
        book.update_peg_price(8)

        # enter sell order at $10 for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(1, 10, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [])

        # enter aggressive pegged buy order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(2, 12, 2, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])

        # move peg point so pegged order crosses
        (crossed_orders, new_bbo) = book.update_peg_price(11)
        self.assertEqual(crossed_orders, [((2, 1), 10, 2)])

        # book should be empty
        self.assertEqual(len(book.bids), 0)
        self.assertEqual(len(book.asks), 0)
        self.assertEqual(len(book.pegged_bids), 0)
        self.assertEqual(len(book.pegged_asks), 0)

    def test_peg_crosses_peg_buy(self):
        book = IEXBook()
        book.update_peg_price(8)

        # enter aggressive pegged sell order for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(1, 4, 2, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])

        # enter aggressive pegged buy order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(2, 10, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [((2, 1), 8, 1)])

        # enter aggressive pegged buy order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(3, 10, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [((3, 1), 8, 1)])

        self.assertEqual(len(book.pegged_bids), 0)
        self.assertEqual(len(book.pegged_asks), 0)

    def test_peg_crosses_peg_sell(self):
        book = IEXBook()
        book.update_peg_price(8)

        # enter aggressive pegged buy order for 2 units
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(1, 10, 2, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [])

        # enter aggressive pegged sell order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(2, 4, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [((2, 1), 8, 1)])

        # enter aggressive pegged sell order with volume 1
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(3, 4, 1, True, midpoint_peg=True)
        self.assertEqual(crossed_orders, [((3, 1), 8, 1)])

        self.assertEqual(len(book.pegged_bids), 0)
        self.assertEqual(len(book.pegged_asks), 0)
    
    def test_cross_multiple_orders_buy(self):
        book = IEXBook()
        book.update_peg_price(11)

        # enter sell order at $10 for 1 unit
        book.enter_sell(1, 10, 1, True, midpoint_peg=False)
        # enter pegged sell order for 1 unit
        book.enter_sell(2, 4, 1, True, midpoint_peg=True)
        # enter sell order at $13 for 2 units
        book.enter_sell(3, 13, 1, True, midpoint_peg=False)

        # enter buy at $14, volume 1. should only cross with order 1
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(4, 14, 1, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((4, 1), 10, 1)])

        # replace order 1
        book.enter_sell(1, 10, 1, True, midpoint_peg=False)

        # enter buy at $14, volume 2. should cross with orders 1 and 2
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(4, 14, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((4, 1), 10, 1), ((4, 2), 11, 1)])

        # replace orders 1 and 2
        book.enter_sell(1, 10, 1, True, midpoint_peg=False)
        book.enter_sell(2, 4, 1, True, midpoint_peg=True)

        # enter buy at $14, volume 3. should cross with orders 1, 2 and 3
        (crossed_orders, entered_order, new_bbo) = book.enter_buy(4, 14, 3, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((4, 1), 10, 1), ((4, 2), 11, 1), ((4, 3), 13, 1)])

        # book should be empty
        self.assertEqual(len(book.bids), 0)
        self.assertEqual(len(book.asks), 0)
        self.assertEqual(len(book.pegged_bids), 0)
        self.assertEqual(len(book.pegged_asks), 0)

    def test_cross_multiple_orders_sell(self):
        book = IEXBook()
        book.update_peg_price(11)

        # enter buy order at $13 for 1 unit
        book.enter_buy(1, 13, 1, True, midpoint_peg=False)
        # enter pegged buy order for 1 unit
        book.enter_buy(2, 15, 1, True, midpoint_peg=True)
        # enter buy order at $10 for 2 units
        book.enter_buy(3, 10, 1, True, midpoint_peg=False)

        # enter sell at $4, volume 1. should only cross with order 1
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(4, 4, 1, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((4, 1), 13, 1)])

        # replace order 1
        book.enter_buy(1, 13, 1, True, midpoint_peg=False)

        # enter sell at $4, volume 2. should cross with orders 1 and 2
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(4, 4, 2, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((4, 1), 13, 1), ((4, 2), 11, 1)])

        # replace orders 1 and 2
        book.enter_buy(1, 13, 1, True, midpoint_peg=False)
        book.enter_buy(2, 15, 1, True, midpoint_peg=True)

        # enter sell at $4, volume 3. should cross with orders 1, 2 and 3
        (crossed_orders, entered_order, new_bbo) = book.enter_sell(4, 4, 3, True, midpoint_peg=False)
        self.assertEqual(crossed_orders, [((4, 1), 13, 1), ((4, 2), 11, 1), ((4, 3), 10, 1)])

        # book should be empty
        self.assertEqual(len(book.bids), 0)
        self.assertEqual(len(book.asks), 0)
        self.assertEqual(len(book.pegged_bids), 0)
        self.assertEqual(len(book.pegged_asks), 0)


if __name__ == '__main__':
    unittest.main()