from OuchServer.ouch_server import ProtocolMessageServer
from UTPServer.utp_messages import UTPMessages
from UTPServer.utp_feed import Feed, BCSFeedUnit

import asyncio
import asyncio.streams
import configargparse

class UTPServer(ProtocolMessageServer):

    def __init__(self, feed_source_file):
        super().__init__(UTPMessages)
        self.feed_source_file = feed_source_file

    async def _handle_client_requests(self, client_token, client_reader):
        """
        """
        feed = Feed(BCSFeedUnit)
        feed.from_csv(self.feed_source_file)
        client = self.clients[client_token]
        for time_to_sleep, line in feed:
            await asyncio.sleep(time_to_sleep)
            client.writer.write(line)
            await client.writer.drain()
        client.writer.close()

def main():
    loop = asyncio.get_event_loop()
    server = UTPServer('UTPServer/test_data/test.csv')
    server.start(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()

