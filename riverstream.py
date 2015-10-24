from datetime import datetime


DEFAULT_LAST_VALUE = 0


class RiverStream(object):

  
  def __init__(self, client, dataId, since=None, until=None, limit=5000):
    riverName = dataId[0]
    streamName = dataId[1]
    self._id = dataId
    self._client = client
    self._stream = self._client.river(riverName).stream(streamName)
    self._field = dataId[2]
    self._dataHandle = None
    self._data = []
    self._headers = []
    # The cursor is the position next value.
    self._cursor = 0
    self._since = since
    self._until = until
    self._limit = limit
    self._lastValue = DEFAULT_LAST_VALUE
    self._min = None
    self._max = None


  def __len__(self):
    return len(self._data) - self._cursor


  def _fetchNextData(self):
    print "Loading next data cursor for %s..." % self.getName()
    self._dataHandle = self._dataHandle.next()
    self._cursor = 0
    self._data = self._dataHandle.data()
    self._headers = self._dataHandle.headers()
    print "Loaded %i rows." % len(self)


  def _updateMinMax(self, value):
    min = self._min
    max = self._max
    if min is None or value < min:
      self._min = value
    if max is None or value > max:
      self._max = value


  def load(self):
    print "Loading data for %s..." % self.getName()
    self._dataHandle = self._stream.data(
      since=self._since, until=self._until, limit=self._limit
    )
    self._data = self._dataHandle.data()
    self._headers = self._dataHandle.headers()
    print "Loaded %i rows." % len(self)


  def next(self):
    out = self.peek()[self._headers.index(self._field)]
    self._cursor += 1
    if out is not None:
      self._lastValue = out
    return out


  def last(self):
    return self._lastValue


  def peek(self):
    if len(self) is 0:
      raise Exception("RiverStream object is empty!")
    return self._data[self._cursor]


  def advance(self, myDateTime):
    if self.getTime() == myDateTime:
      out =  self.next()
      # Sometimes, the stream has no value for this field and returns None, in 
      # this case we'll use the last value as well.
      if out is None:
        out = self.last()
    else:
      out = self.last()
    # If there's no more data, we must fetch more
    if len(self) is 0:
      self._fetchNextData()
    
    self._updateMinMax(out)
    
    return out


  def getName(self):
    return " ".join(self._id)


  def getTime(self):
    headers = self._headers
    timeStringIndex = headers.index("datetime")
    timeString = self.peek()[timeStringIndex]
    return  datetime.strptime(timeString, "%Y/%m/%d %H:%M:%S")


  def createFieldDescription(self):
    return {
      "fieldName": self.getName(),
      "fieldType": "float",
      "minValue": self._min,
      "maxValue": self._max
    }


  def __str__(self):
    return self.getName()