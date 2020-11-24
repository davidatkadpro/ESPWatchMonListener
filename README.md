# ESPWatchMonListener
Watchmon micropython module for parsing UDP messages

This module is based off [WatchMonUdpListener](https://github.com/Batrium/WatchMonUdpListener) from [Daniel Römer](https://github.com/daromer2)

## Install
Save the module to your ESP32 or similar micropython device.
You can use [uPyCraft](https://github.com/DFRobot/uPyCraft) or [webrepl](http://micropython.org/webrepl) to loaded the module to your device.

install the msg_...json files to the same directory `/watchmon`. you will likely need to use the web repl for this as uPyCraft doesnt like .json files.
once loaded you can move them from the `/` dir to `/watchmon` dir by:
```
import uos
uos.rename(/msg...json, /watchmon/msg...json)
```
## How to use
Import the module
```
from watchmon import Watchmon
```
### Module Arguments
The module takes `host`, `port`, `buf_size`, `blocking`, `callback`, `callint`, `sleep`, `msgdir` and `active_codes`.

##### host
This can be left blank default(`""`) as it should default to the sockets host.

##### port
This is the default port Watchmon client is publishing too (default `18542`).

##### buf_size
This is the size of the socket read buffer (default `1024`).

##### blocking
Set this to `True` if you want to wait on the socket for messages, this will block other action and render the `sleep` argument useless (default `False`).

##### callback
You can pass a callback that can be called when the call interval `callint` is achieved, this callback takes one argument and gets passed the response with all the cached messages revieved.
```
def wmCallback(res):
  for msg in res:
    #perform an action like mqtt publish
```
##### callint
This is the interval in seconds that the `callback` is called, set to `0` to call on every incoming message (default `5`sec).

##### sleep
Set `sleep` to the amount of time between reading messages from the port, this is especally usefull to filter the amount of incoming messages as to to overwhelm the device.
It is also usefule if you run the device in and asynchronous coroutine to you can perform other tasks in this time (default `300`ms).

##### msgdir
This is the directory that the messages in json format are stored, if not under the root you can specify the folder here (default `"./watchmon"`)

##### active_codes
Here is where you specify the actural messages you want to add to the buffer, here you can also filter down what onces you do want or you can just install the message .json files that you want to read. This takes a list (default `['3e32', '3f33', '415a']`).

### Initialize an instance
```
def wmCallback(res):
  for msg in res:
    print(msg, res[msg])
    
wm = Watchmon(callback=wmCallback)
```
### Connect
```
wm.connect()
```
### Run continuously 
```
#continuously
wm.run()

#single time
wm.run(True)
```
### Run asynchronous 
```
import uasyncio as asyncio
from watchmon import Watchmon

def wmCallback(res):
  for msg in res:
    print(msg, res[msg])

async def main():
  wm = Watchmon(callback=wmCallback)
  asyncio.create_task(wm.arun())
  await asyncio.sleep(0)

def run():
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print('Interrupted')
  finally:
    asyncio.new_event_loop()
run()

```
### Add MQTT the callback
You may need to install the umqtt.simple module depending on your micropython firmware.
```
from umqtt.simple import MQTTClient
import utime as time

client = MQTTClient(client_id, server, port, mq_user, mq_pass)

while client.connect(True):
  time.sleep_ms(100)
  
def wmCallback(res):
  for msg in res:
    client.publish(msg.encode(), res[msg].encode())
```
