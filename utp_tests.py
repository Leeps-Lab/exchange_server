from UTPServer.utp_feed import *
import time
from random import randrange


if __name__ == '__main__':
    feed = Feed(BCSFeedUnit)
    feed.from_csv('UTPServer/test_data/test.csv')
    print(feed)
    for row in feed:
        print(row)
