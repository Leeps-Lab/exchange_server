import asyncio
from UTPServer.utp_messages import UTPMessages

host, port = '127.0.0.1', 12345

async def subscribe_utp_feed(loop):
    reader, _ = await asyncio.streams.open_connection(
        host, port, loop=loop
    )
    while True:
        try:
            utp_header_bytes = await reader.readexactly(3)
        except asyncio.IncompleteReadError:
            break
        print('header: %s' % utp_header_bytes)  
        try:
            utp_payload_bytes = await reader.readexactly(76)
        except asyncio.IncompleteReadError:
            break
        print('payload: %s' % utp_payload_bytes)   
        utp_message = UTPMessages.LongFormQuoteMessage.from_bytes(utp_payload_bytes, header=False)
        print('messsage content: {}'.format(list(utp_message.iteritems())))

def main():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(subscribe_utp_feed(loop), loop=loop)
    try:
        loop.run_forever()
    finally:
        loop.close()
    

if __name__ == '__main__':
    main()
    