import re

import config
from transport import *
import wave
import contextlib
import pyaudio
import os


class Announcement:
    def __init__(self):
        self.path = config.base_path + config.language

    def getGeneralBlocks(self, string: str) -> str:
        genericpaths = {
            "gong": "/../gong/513/513_1.wav",
            "gleis": "/module_3_1/016.wav",
            "einfahrt": "/module_3_1/012.wav",
            "nach": "/module_3_1/032.wav",
            "abfahrt": "/module_3_1/001.wav",
            "abfahrt_ursprünglich": "/module_3_1/002.wav",
            "vorsicht_bei_der_einfahrt": "/module_3_1/046.wav",
            "über": "/module_3_1/035.wav",
            "achtung_am_gleis": "/module_3_1/153.wav",
            "achtung_am_bahnsteig": "/module_3_1/154.wav",
            "ein_zug_fährt_durch_wg": "/module_3_1/155.wav",
            "ein_zug_fährt_durch_wb": "/module_3_1/156.wav",
            "ein_zug_fährt_ein_wg": "/module_3_1/157.wav",
            "ein_zug_fährt_ein_wb": "/module_3_1/158.wav",
            "ein_zug_fährt_durch": "/module_3_1/159.wav",
            "ein_zug_fährt_ein": "/module_3_1/160.wav",
            "information_zu": "/module_3_1/030.wav",
            "ihre_nächsten_anschlüsse": "/module_3_1/026.wav",
            "von_gleis": "/module_3_1/039.wav",
            "und": "/module_3_1/036.wav",
            "von": "/module_3_1/038.wav"
        }
        return self.path + genericpaths[string.lower()]

    def getNumber(self, number: str, pron: chr = 'h') -> list:
        pron = self.getPronPath(pron)
        containsLetters = any(c.isalpha() for c in number)
        platformNumber: str = number
        if containsLetters:
            platformNumber = re.findall(r'\d+', number)[0]
        output: list = []

        if len(platformNumber) < 3:
            # zwei- oder wenigerstellige zahl, ganz normal
            output.append(f'{self.path}/gleise_zahlen/{pron}/{number}.wav')
        elif len(platformNumber) == 3:
            output.append(f'{self.path}/gleise_zahlen/{pron}/{number[0]}00_.wav')
            if number[1] == "0":
                if number[2] == "0":
                    output = [f'{self.path}/gleise_zahlen/{pron}/{number[0]}00.wav']
                else:
                    output.append(f'{self.path}/gleise_zahlen/{pron}/{number[2]}.wav')
            else:
                output.append(f'{self.path}/gleise_zahlen/{pron}/{number[1:]}.wav')
        else:
            # error.
            print(f'Error: Platform Number {platformNumber} could not be spoken')
            raise Exception
        return output

    def getTrainType(self, line: Line, pron: chr = 'h') -> str:
        pron = self.getPronPath(pron)
        """output: list = []
        lineName: str = ""
        if len(line.productName) == 1:
            lineName = line.productName
        else:
            lineName = '_'.join([c for c in line.productName])"""
        return f'{self.path}/zuggattungen/{pron}/{line.productName.lower()}.wav'

    def getTrainNumber(self, line: Line, pron: chr = 'h') -> list:
        lineNumber = ""
        result = ""
        for char in reversed(line.name):
            if char.isdigit():
                result = char + result
            else:
                if result:
                    break
        return self.getNumber(result, pron)

    def getStationName(self, stopStation = None, pron: chr = 'h') -> str:
        path = f'{self.path}/ziele/variante1/{self.getPronPath(pron)}/{stopStation.id}.wav'
        if os.path.isfile(path):
            return path
        else:
            return f'{self.path}/ziele/variante1/{self.getPronPath(pron)}/{stopStation.id}.wav'

    def getHour(self, hour: str, pron: chr = 'h') -> str:
        di = "{:02d}".format(hour)
        return f'{self.path}/zeiten/stunden/{self.getPronPath(pron)}/{di}.wav'

    def getTime(self, time: datetime.datetime, pron: chr = 'h') -> list:
        return [self.getHour(int(time.strftime("%H"))),
                self.getMinute(int(time.strftime("%M")), pron)]

    def getMinute(self, minute: str, pron: chr = 'h') -> str:
        di = "{:02d}".format(minute)
        return f'{self.path}/zeiten/minuten/{self.getPronPath(pron)}/{di}.wav'

    def getPronPath(self, pron: chr):
        """
        Gives back the path which specifies the pronounciation (high or low)
        :param pron: chr with 'h' for high pronounciation and 't' or 'l' for low pronounciation
        :return: "hoch" or "tief"
        """
        if pron == 't' or pron == 'l':
            return 'tief'
        else:
            return 'hoch'

    def getTrip(self, stop: Stop, trip: Trip):

        stop = stop
        if not trip: trip = stop.trips[0]
        queque = []

        queque.append(self.getTrainType(trip.line))
        queque.extend(self.getTrainNumber(trip.line))
        stopIdToQueque = trip.destination.id
        if trip.destination.id == stop.id:
            queque.append(self.getGeneralBlocks("von"))
            trip.getOrigin()
            stopIdToQueque = trip.origin.id
        else:
            queque.append(self.getGeneralBlocks("nach"))

        # Über
        via = trip.getVia(stop.id)
        if via:
            queque.append(self.getStationName(Station(stopIdToQueque), 'h'))
            queque.append(self.getGeneralBlocks("über"))
            queque.append(self.getStationName(via, 't'))
        else:
            queque.append(self.getStationName(Station(stopIdToQueque), 'l'))

        if trip.delay > 120:
            # Verspätung, "Abfahrt ursprünglich"
            queque.append(self.getGeneralBlocks("abfahrt_ursprünglich"))
            queque.extend(self.getTime(trip.departureTime, 'l'))
        else:
            # Keine Verspätung
            queque.append(self.getGeneralBlocks("abfahrt"))
            queque.extend(self.getTime(trip.departureTime, 'l'))
        return queque

    def getDelay(self, trip: Trip) -> str:
        rmins = 0
        if trip.delay < 3:
            rmins = 0
        elif trip.delay < 60:
            rmins = 5 * round(trip.delay / 5)
        elif trip.delay < 200:
            rmins = 10 * round(trip.delay / 10)
        else:
            rmins = 210
        if rmins == 0:
            return []
        rmins = di = "{:03d}".format(rmins)
        return f'{self.path}/zeiten/verspaetung_heute/{rmins}.wav'


class DepartureAnnouncement(Announcement):
    def __init__(self, stop: Stop, trip: Trip = None):
        super().__init__()
        self.stop = stop
        if not trip:
            self.trip = self.stop.trips[0]
        else:
            self.trip = trip

        self.queque: list = []
        self.queque = []
        self.queque.append(self.getGeneralBlocks("gong"))
        self.queque.append(self.getGeneralBlocks("gleis"))
        self.queque.extend(self.getNumber(self.trip.platform))
        self.queque.append(self.getGeneralBlocks("einfahrt"))
        self.queque.extend(self.getTrip(self.stop, self.trip))
        self.queque.append(self.getGeneralBlocks("vorsicht_bei_der_einfahrt"))
        play_wav_files(self.queque)


class TrainPassageAnnouncement(Announcement):
    def __init__(self, track: int = None, passingIn: bool = False):
        super().__init__()
        self.queque = []
        self.queque.append(self.getGeneralBlocks("gong"))
        if track:
            self.queque.append(self.getGeneralBlocks("achtung_am_gleis"))
            self.queque.extend(self.getNumber(str(track)))
            if not passingIn:
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_durch_wg"))
                self.queque.extend(self.getNumber(str(track)))
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_durch"))
            else:
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_ein_wg"))
                self.queque.extend(self.getNumber(str(track)))
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_ein"))

        elif not track:
            self.queque.append(self.getGeneralBlocks("achtung_am_bahnsteig"))
            if not passingIn:
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_durch_wb"))
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_durch"))
            else:
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_ein_wb"))
                self.queque.append(self.getGeneralBlocks("ein_zug_fährt_ein"))
        else:
            raise Exception
        play_wav_files(self.queque)


class Information(Announcement):
    def __init__(self, stop: Stop, trip: Trip, infoType: str = 'delay'):
        super().__init__()
        self.queque = []
        self.stop = stop
        self.trip = trip
        match infoType:
            case 'delay':
                self.doDelayAnnouncement()
        play_wav_files(self.queque)

    def doDelayAnnouncement(self):
        self.queque.append(self.getGeneralBlocks("information_zu"))
        self.queque.extend(self.getTrip(self.stop, self.trip))
        self.queque.append(self.getDelay(self.trip))
        rmins = 0


class NextConnections(Announcement):
    def __init__(self, stop: Stop):
        super().__init__()
        self.stop = stop
        if self.stop.trips is None or self.stop.trips == []:
            return

        self.queque = []
        self.queque.append(self.getGeneralBlocks("gong"))
        self.queque.append(self.getGeneralBlocks("ihre_nächsten_anschlüsse"))
        ftrips = stop.trips[0:6]
        for i, e in enumerate(ftrips):
            self.queque.extend(self.getTrip(self.stop, e))
            self.queque.extend(self.getDelay(e))
            self.queque.append(self.getGeneralBlocks("von_gleis"))
            self.queque.extend(self.getNumber(e.platform, 'l'))
            if i == len(ftrips)-2:
                self.queque.append(self.getGeneralBlocks("und"))

        play_wav_files(self.queque)




def play_wav_files(files):
    chunk = 1024
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)

    for filename in files:
        # try:
        with contextlib.closing(wave.open(filename, 'rb')) as wf:
            rate = wf.getframerate()
            nchannels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            stream = p.open(format=p.get_format_from_width(sampwidth),
                            channels=nchannels,
                            rate=rate,
                            output=True)
            data = wf.readframes(chunk)
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
        # except: pass
    stream.stop_stream()
    stream.close()
    p.terminate()

####### Just for testing purposes #######

thisStop = Stop('8002347')
thisStop.getTrips()
x = NextConnections(thisStop)
#t = DepartureAnnouncement(thisStop, thisStop.trips[0])
#y = TrainPassageAnnouncement(3)

for i in thisStop.trips:
    if i.delay >= 3:
        print(f'Trip to {i.destinationName} is delayed')
        t = Information(thisStop, i)
    else:
        print(f'Trip to {i.destinationName} is not delayed ({i.delay})')
