import socket as socket
import ustruct as struct
import uasyncio as asyncio
import utime as time
import ujson as json

class Watchmon:
    def __init__(self, host="", port=18542, buf_size=1024, blocking=False,  callback=None, callint=5, sleep=300, msgdir='watchmon/', active_codes=[]):
        self.host = host
        self.port = port
        self.buf_size = buf_size
        self.blocking = blocking
        self.callback = callback
        self.callint = callint
        self.sleep = sleep
        self.msgdir = msgdir
        self.active_codes = active_codes
        self._sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
        self._buffer = {}
        self._last_call = time.ticks_ms()
        
    def _packetInfo(self, data):
        data = struct.unpack("<shshh", data[:8])
        payload = {
            'msg_id': hex(data[1]).rstrip("L").lstrip("0x"),        
            'sys_id': data[3],
            'hub_id': data[4]
        }
        return payload
        
    def connect(self):
        self._sock.bind((self.host, self.port))
        self._sock.setblocking(self.blocking)
        
    def disconnect(self):
        self._sock.close()

    def packetMsg(self):
        if self._buffer != {}:
            import uos as os
            _ld = os.listdir(self.msgdir)
            _files = {d.split('_')[1]: [d, d.split('_')[2][:-5]] for d in _ld if d.startswith('msg') and d.endswith('.json')}
            msg = {}
            for packet in self._buffer:
                if packet in _files:
                    _parse = []
                    with open(self.msgdir+_files[packet][0], 'r') as f:
                        _parse = json.load(f)
                    _p_data = self._buffer[packet]
                    msg[_files[packet][1]] = self._packetParse(self._buffer[packet], _parse)
            self._buffer = {}
            gc.collect()
            return msg
        else:
            return None


    def _packetParse(self, _data, _parser, _sub=False): 
        _package = {}   
        _data, _data_sub = _data if type(_data) == list else [_data, None]

        _skip_d = [0,0]
        for i, v in enumerate(_parser):
            if not _sub:
                ii = _skip_d[0] + i
            elif _sub:
                ii = _skip_d[1] + i
            else:
                ii = i
            if len(v) > 1:
                if type(v[1]) == list and _data_sub != None:
                    _package[v[0]] = []
                    for ds in _data_sub:                        
                        _package[v[0]].append(self._packetParse(ds, v[1]))
                elif type(v[1]) == str and v[0] != 'skip':                                    
                    _package[v[0]] = _formatter(_data[ii], v[1])
                elif type(v[1]) == int and v[0] == 'skip':
                    if not _sub:
                        _skip_d[0] += (v[1] -1)
                    else:
                        _skip_d[1] += (v[1] -1)               
            else:
                _package[v[0]] = _data[ii]
        return _package

    def _packetStore(self, _id, _packet):
        _data = self._packetDecode(_id, _packet) 
        if _data != None:
            self._buffer[_id] =_data

    def _packetDecode(self, _id, _packet):
        _packet = _packet[8:]
        if _id in wm_codes:
            if len(self.active_codes) > 0 and _id not in self.active_codes:
                return None
            _format = wm_codes[_id][0]
            _sub_f = wm_codes[_id][1] if len(wm_codes[_id]) > 1 else False
            _len = struct.calcsize(_format)
            _data = struct.unpack(_format, _packet[:_len])
            _remaining = _packet[_len:]
            if _sub_f:
                _sub_d = []
                _sub_l = struct.calcsize(_sub_f)
                while len(_remaining) > 0:
                    _d = struct.unpack(_sub_f, _remaining[:_sub_l])
                    _sub_d.append(_d)
                    _remaining = _remaining[_sub_l:]
                _data = [_data, _sub_d]
            return _data        

    def run(self, uasync=False):
        while True:
            try:
              _data, _addr = self._sock.recvfrom(self.buf_size)
              info = self._packetInfo(_data)              
              self._packetStore(info['msg_id'], _data)              
            except OSError:
              pass

            if self.callback != None and len(self._buffer) > 0:
                _now = time.ticks_ms()
                if (_now - self._last_call) > (self.callint * 1000):
                    self._last_call = _now
                    self.callback(self.packetMsg())
            if uasync:
                return
            else:
                time.sleep_ms(self.sleep)

    async def arun(self):
        while True:
            self.run(True)

            await asyncio.sleep_ms(self.sleep)


x = 0
def _formatter(c, calc):
    global x
    x = c
    if len(calc) > 32:
        return 0
    return eval(calc)

wm_codes = {
'3e32': ['<hh6Bhh6Bh10Bhff'],
'3e5a': ['<hh6Bhh6Bh10BhfBB'],
'3f33': ['<5Bhh8BhBIBBff12Bhh5Bhhff3Bh'],
'4032': ['<I16Bhh3fBBIhh8bf'],
'415a': ['<4B', '<BBhhBBhB'],
'4232': ['<BBhhBBh4B4h3B3hIIfB'],
'4732': ['<71B'],
'475a': ['<71B'],
'4932': ['<4B6h3I1bB6hIII'],
'4a34': ['<h8s20s20sBBI3hI'],
'4a35': ['<h8s20s20sBBI3hIBB'],
'4b34': ['<4B5h9BhBf3hBhhh'],
'4b35': ['<4B5h9BhBf3hB4h'],
'4c33': ['<B4h7B5fBBffhhh'],
'4c58': ['<B4h7B5fBB'],
'4d33': ['<20Bhh'],
'4d34': ['<20Bhh'],
'4e58': ['<18hB'],
'4f33': ['<5Bhh6Bhh7B3hBhhBhh4IBB3hB'],
'5033': ['<4Bhh9BhhB3hB3h3BIIBfB'],
'5158': ['<11BhhB3hB3h3BIIB'],
'5258': ['<5BII6BIIB'],
'5334': ['<6BIII'],
'5431': ['<IhhIBhh'],
'5432': ['<4hBBhh18BhhBii4f'],
'5457': ['<4hBBhh18BhhBiiff'],
'5632': ['<9Ih15IBII'],
'5732': ['<8shhi7B3h5BhfBB'],
'5831': ['<hIB1b4B6h16B4h'],
'6131': ['<IBBhh15B'],
'6132': ['<IBBhh16B'],
'6831': ['<hIBB3hBhhfB'],
'7857': ['<B5IBBhh3fIIhh8s8s']
}
