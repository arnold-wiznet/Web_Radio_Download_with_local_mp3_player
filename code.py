import sys
import time
import os 
import board
import math
import storage
from digitalio import DigitalInOut,Direction
from analogio import AnalogIn
import adafruit_connection_manager
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
import sdcardio
import gc
print("Memory = ", gc.mem_free())

# Initialize spi interface
import busio
cs = DigitalInOut(board.GP17)
spi_bus = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs)

# # Change Mac Address of the device if multiple Pico boards are connected
# eth.mac_address = bytearray([0x00, 0x08, 0xDC, 0x22, 0x33, 0x71])


# #Initialize a requests session
pool = adafruit_connection_manager.get_radio_socketpool(eth)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
requests = adafruit_requests.Session(pool, ssl_context)


# Mounting SD Card
spi_bus_2 = busio.SPI(board.GP14, MOSI=board.GP15, MISO=board.GP12)
sd = sdcardio.SDCard(spi_bus_2, board.GP13)
vfs = storage.VfsFat(sd)
storage.mount(vfs, '/sd')
#print(os.listdir('/sd'))

button = DigitalInOut(board.GP0)
button.direction = button.direction.INPUT
path_mp3 = "/sd/demo2.mp3"
data_list = bytearray()


power = True
new_file = True
i = 0
available_url = {
    "JapanHits": "https://cast1.torontocast.com/JapanHits",
    "JSakura" : "https://cast1.torontocast.com/jsakura",
    "Anime" : "https://animefm.stream.laut.fm/animefm",
    "Future Groove": "https://streamer.radio.co/s4b3dafa6d/listen",
    "Vocaloid": "https://vocaloid.radioca.st/stream",
    "J-Pop Project Radio": "https://15113.live.streamtheworld.com/SAM10AAC139.mp3?dist=onlineradiobox",
    "HK Latino Radio" : "https://stream-174.zeno.fm/rvd3ef4x2tzuv?zt=eyJhbGciOiJIUzI1NiJ9.eyJzdHJlYW0iOiJydmQzZWY0eDJ0enV2IiwiaG9zdCI6InN0cmVhbS0xNzQuemVuby5mbSIsInJ0dGwiOjUsImp0aSI6IlYxV1pQMXJKUjFxQzF0RjNXbHZfZWciLCJpYXQiOjE3NDQ4NzkyNzgsImV4cCI6MTc0NDg3OTMzOH0.sPoNJiFDXzP9sZZuvjRt-eUzSX9r2cgZvUPXHe-4pN4",
    "Dubstep" : "https://s2.radio.co/s30844a0f4/listen",
    "house" : "https://streaming.radio.co/s06bd9d805/listen",
    "EDM Session" : "https://s2.radio.co/s30844a0f4/listen"
}



#Section Download
while power:
    
    r = requests.get(available_url["JapanHits"], stream = True) 
    if r.status_code == 200:
        start_time = time.time()
        try:
            for chunk in r.iter_content(1024):

                try:
                    

                    data_list.extend(chunk)
                    
                    if button.value == 0:
                        
                        power = False
                        break
                except MemoryError:
                    i = i + 1
                    
                    if new_file:
                        with open(path_mp3,"wb") as f:
                            f.write(data_list)
                        new_file = False
                    else:
                        with open(path_mp3,"ab") as f:
                           f.write(data_list)
                    data_list = bytearray()
                    data_list.extend(chunk)
                    end_time = time.time()
                    latency = end_time - start_time
                    print("Latency Write Same Chunk: ", latency, "s.")  
                        
        except OSError:
                print("OS ERROR HERE")
                if new_file:
                    with open(path_mp3,"wb") as f:
                        f.write(data_list)
                    new_file = False
                else:
                    with open(path_mp3,"ab") as f:
                       f.write(data_list)
                data_list = bytearray()
                data_list.extend(chunk)


        if new_file:
            with open(path_mp3,"wb") as f:
                f.write(data_list)
                new_file = False
        else:
            with open(path_mp3,"ab") as f:
                f.write(data_list)
        data_list = bytearray()
        data_list.extend(chunk)
        end_time = time.time()
        print("Latency Request: ", end_time - start_time, "s.") 

    else:
        print("Link is unavailable.")
        print(r.status_code)
        power = False
r.close()
r = None


# sys.exit()



knob = AnalogIn(board.A1)
button2 = DigitalInOut(board.GP3)
button2.direction = button2.direction.INPUT

state = True 
from audiomp3 import MP3Decoder
from audiopwmio import PWMAudioOut as AudioOut

audio = AudioOut(board.A0)

previous_state = None
if os.stat(path_mp3):
    
    mp3 = open(path_mp3, "rb")
    # audio = AudioOut(board.A0)
    decoder = MP3Decoder(mp3)
    
    import audiomixer
    mixer = audiomixer.Mixer(voice_count = 1, sample_rate = decoder.sample_rate, channel_count = decoder.channel_count, bits_per_sample = decoder.bits_per_sample, samples_signed = True, buffer_size = 1024*2)

    decoder.file = open(path_mp3,"rb")
    while True:
        print(button2.value)
        if not button2.value:
            break
        if not button.value:
            print("Playing")
            audio.play(mixer)
            mixer.voice[0].play(decoder)

            while mixer.playing:
                if button2.value == 0 and previous_state == True:
                    
                    state = not state
                    if state :
                        print("Resume")
                        audio.resume()
                    else:
                        print("Paused")
                        audio.pause()
                v = ((round(knob.value,-2) - 800) / (65500 - 800)) ** 0.6
                # print(mixer.voice[0].level)
                if not isinstance(v, complex):
                    mixer.voice[0].level = v
                else:
                    mixer.voice[0].level = 0
                previous_state = button2.value
                time.sleep(.1)
            print("Song Finished.")
        time.sleep(.1)       
    decoder.file.close()
    mp3.close()

