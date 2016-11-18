import asyncio
import configargparse
import logging as log
from functools import partial
from OuchServer.ouch_server import ProtocolMessageServer
from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
from exchange.order_books.cda_book import CDABook
from exchange.exchange import Exchange

p = configargparse.getArgParser()
p.add('--port', default=12345)
p.add('--host', default='127.0.0.1', help="Address to bind to / listen on")
p.add('--debug', action='store_true')
p.add('--mechanism', choices=['cda', 'fba'], default = 'cda')
p.add('--interval', default = None, type=float, help="(FBA) Interval between batch auctions in seconds")
options, args = p.parse_known_args()


def main():    
    log.basicConfig(level= log.DEBUG if options.debug else log.INFO,
        format = "[%(asctime)s.%(msecs)03d] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt = '%H:%M:%S')

    loop = asyncio.get_event_loop()
    server = ProtocolMessageServer(OuchClientMessages)
    
    if options.mechanism == 'cda':        
        book = CDABook()
        exchange = Exchange(order_book = book,
                            order_reply = server.send_server_response,
                            loop = loop)
    elif options.mechanism == 'fba':
        book = FBABook()
        exchange = FBAExchange(order_book = book,
                            order_reply = server.send_server_response,
                            loop = loop, 
                            interval = options.interval)
    
    server.register_listener(exchange.process_message)
    server.start(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    main()
