import csv
from collections import deque


class FeedUnit:
    desc = ''
    __slots__ = ()

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
        return cls(**kwargs)
  
    def dictize(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def post_read(self):
        pass
        

class BCSFeedUnit(FeedUnit):
    desc = 'time, fundamental value (V) pairs' 
    __slots__ = ('time', 'fundamental', 'nbo', 'nbb')

    def post_read(self, d_up=50, d_down=50):
        V = self.fundamental = int(self.fundamental)
        self.nbo = V + d_up
        self.nbb = V - d_down
    
    def __str__(self):
        return str(self.dictize())

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
                line.post_read()
                self.feed.append(line)

    def __iter__(self):
        return next(self)

    def __next__(self):
        yield from reversed(self.feed)


    

        
