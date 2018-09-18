from UTPServer import utp_messages, utp_feed
import time

def test_message():
    msg = utp_messages.UTPClientMessages.LongFormQuoteMessage(
        orig = b'D',   # FINRA
        submarket_id = b'L', 
        sip_time = int(time.time()),
        timestamp_1 = int(time.time()),
        part_token = 95060000,
        timestamp_2 = int(time.time()),
        symbol = b'LEEPS',
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