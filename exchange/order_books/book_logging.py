

class BookLogger():
    def __init__(self, book_logfile):
        self.book_logfile = book_logfile

    def book_to_logstring(self, book):
        return "{{'Bids':{}, 'Asks':{}}}".format(
            ["{{'price':{price}, 'orders':{orders}}}".format(
                    price=b.price, 
                    orders=list(b.order_q.items())) 
                for b in book.bids.ascending_items()], 
            ["{{'price':{price}, 'orders':{orders}}}".format(
                price=a.price, 
                orders=list(a.order_q.items())) 
                for a in book.asks.ascending_items()]) 

    def log_book(self, book):
        with open(self.book_logfile, "a") as logfile:
            logfile.write("('book':{})\n".format(self.book_to_logstring(book)))

    def log_book_order(self, book, order):
        with open(self.book_logfile, "a") as logfile:
            logfile.write("{{'order':{}, 'book':{}}}\n".format(order, self.book_to_logstring(book)))
