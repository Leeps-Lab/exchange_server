from exchange_server.OuchServer.ouch_server import ProtocolMessageServer
from UTPServer.utp_messages import UTPMessages


def UTPServer(ProtocolMessageServer):

    def __init__(self, UTPMessages):
        super().__init__(UTPMessages)
    
    async def _handle_client_requests(self, client_token, client_reader):
        """
        spit all utp messages to the client
        """
        feed = await self.get_utp_feed()
        while feed:
            message_type = (self._ProtocolMessageTypes
                            .lookup_by_header_bytes(header_bytes))
            payload_size = message_type.payload_size
            try:
                payload_bytes = (await client_reader.readexactly(payload_size))
            except asyncio.IncompleteReadError as err:
                log.error('Connection terminated mid-packet!')
                break

            client_msg = message_type.from_bytes(payload_bytes, header=False)
            print("Message recieved from client: %s" %client_msg)
            client_msg.meta = client_token
            await self.broadcast_to_listeners(client_msg)