import csv
from UTPServer.utp_messages import UTPMessages
from OuchServer.ouch_server import nanoseconds_since_midnight
import logging as log

class FeedUnit:
    desc = ''
    __slots__ = ()
    protocol_cls = None
    protocol_defaults = {}

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, None))
    
    @classmethod
    def from_list(cls, row):
        kwargs = {}
        for field in cls.__slots__:
                kwargs[field] = row.pop(0)
                if not row:
                    break
        kwargs = cls.field_check(**kwargs)
        return cls(**kwargs)

    @classmethod   
    def field_check(cls, **kwargs):
        pass
  
    def dictize(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def __bytes__(self, **defaults):
        bytes_message = {**self.protocol_defaults}
        for slot in self.__slots__:
            if slot in self.protocol_defaults:
                bytes_message[slot] = getattr(self, slot)
        return bytes(self.protocol_cls(**bytes_message))
   
    def __str__(self):
        return str(self.dictize())

class BCSFeedUnit(FeedUnit):
    desc = 'time, best bid and offer in a row.' 
    __slots__ = ('time', 'bid_price', 'ask_price')
    protocol_cls = UTPMessages.LongFormQuoteMessage
    protocol_defaults = {
        'orig':b'D',   # FINRA
        'submarket_id':b'X',
        'msg_type': b'X', 
        'sip_time':nanoseconds_since_midnight(),
        'timestamp_1':nanoseconds_since_midnight(),
        'part_token':95060000,
        'timestamp_2':nanoseconds_since_midnight(),
        'symbol':b'LEEPS',
        'bid_price':1001000,
        'bid_size':1,
        'ask_price':1002000,
        'ask_size':1,
        'quote_condition':b'R',
        'sip_gen_update':b'X',
        'luld_bbo_indicator':b'X',
        'rri':b'X',
        'nbbo_indicator':b'X',
        'luld_nbbo_indicator':b'X',
        'finra_adf_indicator':b'X'
    }

    @classmethod    
    def field_check(cls, **kwargs):
        edited_kwargs = {}
        for k, v in kwargs.items():
            if not isinstance(v, int):
                int_v = int(v)
            edited_kwargs[k] = int_v
        return edited_kwargs

class Feed:

    def __init__(self, feed_unit_cls):
        self.unit_cls = feed_unit_cls
        self.feed = []

    def from_csv(self, filename, header=True):
        with open(filename, 'r') as f:
            raw_feed = list(csv.reader(f))
            if header:  # first row is column names
                self.header = raw_feed[0]
                raw_feed = raw_feed[1:]
            for row in raw_feed:
                line = self.unit_cls.from_list(row)
                self.feed.append(line)

    def __iter__(self):
        line = None
        for row in self.feed:
            try:
                line = bytes(row)
            except Exception as e:
                log.exception('error encoding row, ignoring: %s', e)
            yield line
        
    def __str__(self):
        return '\n'.join(str(feed_unit) for feed_unit in self.feed)
    


    

        
