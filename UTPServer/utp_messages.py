from OuchServer.protocol_message_primitives import  *

class UTPFields(ProtocolFieldEnum):
    version = ('c', 'protocol version')
    msg_category = ('c', 'message category')
    msg_type = ('c', 'message type')
    orig = ('c', 'market center originator id')
    submarket_id = ('c', 'sub market center id')
    sip_time = ('Q', 'sip timestamp')
    timestamp_1 = ('Q', 'participant timestamp')
    part_token = ('Q', 'participant token')
    timestamp_2 = ('Q', 'FINRA timestamp')
    symbol = ('11s', 'symbol')
    bid_price = ('Q', 'bid price')
    bid_size= ('I', 'bid size')
    ask_price = ('Q', 'ask price')
    ask_size = ('I', 'ask size')
    quote_condition = ('c', 'quote condition')
    sip_gen_update = ('c', 'sip generated update flag')
    luld_bbo_indicator = ('c', 'luld bbo indicator')
    rri = ('c', 'retail interest indicator')
    nbbo_indicator = ('c', 'nbbo appendage indicator')
    luld_nbbo_indicator = ('c', 'luld nbbo indicator')
    finra_adf_indicator = ('c', 'finra adf mpid appendage indicator')

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


class UTPMessages(LookupByHeaderBytesMixin, UTPMessageTypeSpec,
                        DuplicateFreeEnum):
    LongFormQuoteMessage = ('{orig}:{submarket_id}:{timestamp_2}:{symbol}',
                    {'version': b'1', 
                    'msg_category': b'Q',
                    'msg_type': b'F'},
                    ['timestamp_2', 'symbol', 'orig', 'submarket_id',
                    'sip_time', 'timestamp_1', 'part_token', 'bid_price', 
                    'bid_size', 'ask_price', 'ask_size', 'quote_condition',
                    'sip_gen_update', 'luld_bbo_indicator', 'rri', 'nbbo_indicator',
                    'luld_nbbo_indicator', 'finra_adf_indicator' ]
            )


