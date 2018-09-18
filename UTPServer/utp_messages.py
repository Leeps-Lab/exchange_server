from OuchServer.protocol_message_primitives import  *

class UTPFields(ProtocolFieldEnum):
    version = ('c', 'protocol version')
    msg_category = ('c', 'message category')
    msg_type = ('c', 'message type')
    orig = ('c', 'market center originator id')
    submarket_id = ('c', 'sub market center id')
    sip_time = ('l', 'sip timestamp')
    timestamp_1 = ('l', 'participant timestamp')
    part_token = ('l', 'participant token')
    timestamp_2 = ('l', 'FINRA timestamp')
    symbol = ('11s', 'symbol')

class UTPHeader(NamedFieldSequence):
    __slots__ = ('version', 'msg_category', 'msg_type')
    _protocol_fields = UTPFields


class UTPPayloadBase(NamedFieldSequence):
    __slots__ = ()
    _protocol_fields = UTPFields
    _display_fmt = None

    
class UTPMessage(ProtocolMessage):
    _HeaderCls = UTPHeader
    _PayloadBaseCls = UTPPayloadBase

class UTPMessageTypeSpec(MessageTypeSpec):
    _MessageCls = UTPMessage

    def __init__(self, display_fmt, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if display_fmt is not None:
            self._PayloadCls._display_fmt = display_fmt

LookupByHeaderBytesMixin = create_attr_lookup_mixin(
    'LookupByHeaderBytesMixin_ClientMsgs', 'header_bytes')


class UTPClientMessages(LookupByHeaderBytesMixin, UTPMessageTypeSpec,
                        DuplicateFreeEnum):
    LongFormQuoteMessage = ('{orig}:{submarket_id}:{timestamp_2}:{symbol}',
                    {'version': b'1', 
                    'msg_category': b'Q',
                    'msg_type': b'F'},
                    ['timestamp_2', 'symbol', 'orig', 'submarket_id',
                    'sip_time', 'timestamp_1', 'part_token'])


