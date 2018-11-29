from UTPServer import utp_messages, utp_feed
import time
from random import randrange

def test_message():
    msg = utp_messages.UTPClientMessages.LongFormQuoteMessage(
        orig=b'D',   # FINRA
        submarket_id=b' ', 
        sip_time=int(time.time()),
        timestamp_1=int(time.time()),
        part_token=95060000,
        timestamp_2=int(time.time()),
        symbol=b'LEEPS',
        bid_price=randrange(50,60),
        bid_size=1,
        ask_price=randrange(50,60),
        ask_size=1,
        quote_condition=b'R',
        sip_gen_update=b' ',
        luld_bbo_indicator=b' ',
        rri=b' ',
        nbbo_indicator=b' ',
        luld_nbbo_indicator=b' ',
        finra_adf_indicator=b' '
    )
    bytes_msg= bytes(msg)
    print('bytes message:{} with length {}.'.format(bytes_msg, len(bytes_msg)))

def test_feed():
    feed = utp_feed.Feed(utp_feed.BCSFeedUnit)
    feed.from_csv('UTPServer/test_data/test.csv')
    for line in feed:
        print(line)

if __name__ == '__main__':
    test_message()
    test_feed()