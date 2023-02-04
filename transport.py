import requests
import sys
import numpy as mp
import datetime
import datetime

from config import *





def gettripinfos(tripId: str) -> dict:
    url = f'{instance}/trips/{tripId}'
    try: dat = requests.get(url).json()
    except:
        print("wrong tripid or something")
        return
    if len(dat) > 0: return dat



class Location:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        if self.lat == None or self.lon == None: return
        self.osmlink = self.getLink()

    def getLink(self, marker=True) -> str:
        link = "https://www.openstreetmap.org/"
        if marker is True: link += f"?mlat={self.lat}"
        if marker is True: link += f"&mlon={self.lon}"
        link += f"#map=17/{self.lat}/{self.lon}"
        return link


class Trip:
    def __init__(self, tripId: str = None , fetchData = True, loadedStation = None, tripData: dict = None, dataType: str = None):
        self.dataType = dataType
        self.tripId = tripId
        if self.tripId == None:
            self.tripId = tripData['tripId']
        if self.tripId == None:
            print("NO TRIPID")
            return
        if '|' not in self.tripId: raise Exception

        if fetchData == False: dat = tripData
        else:
            url = f'{instance}/trips/{tripId}'

            try: dat = requests.get(url).json()['trip']
            except:
                print("wrong tripid or something")
                return

        if len(dat) < 1: raise Exception

        self.tripData = dat
        try:
            self.originName = dat['origin']['name']
            self.origin = Stop(dat['origin'])
        except:
            self.originName = None
            self.originObject = None

        try:
            self.lineName = dat['line']['name']
            self.line = Line(dat['line'])
        except: pass

        # Ziel und Zieltext

        try:
            self.destinationName = dat['destination']['name']
        except:
            try: self.destinationName = dat['direction']
            except: self.destinationName = "error"


        if self.dataType == "arrival" and loadedStation != None:
            # Falls es sich bei den eingegebenen Daten um Daten aus /stop/:id/arrivals
            # handelt, so setze den destinationName auf den zurzeit im Programm geladenen
            # Halt (loadedStation)
            self.destination = loadedStation
            self.destinationName = loadedStation.name
        try:
            self.destination = Stop(dat['destination']['id'], False, dat['destination'])
        except: pass


        if self.dataType == "arrival" or self.dataType == "departure":
            try: self.DOText = dat['origin']
            except: self.DOText = dat['provenance']

            try:
                try: self.when = dat['when']
                except: self.when = dat['plannedWhen']
                try: self.plannedWhen = dat['when']
                except: self.plannedWhen = dat['plannedWhen']
                try:
                    try: self.platform = dat['platform']
                    except: self.platform = dat['plannedPlatform']
                    try: self.plannedPlatform = dat['plannedPlatform']
                    except: self.plannedPlatform = dat['platform']
                except: pass
            except: pass

        else:
            try: self.DOText = dat['stopovers'][0]['stop']['name']
            except: self.DOText = "Error."


        try:self.departureTime = datetime.datetime.fromisoformat(dat['when'])
        except:
            try: self.departureTime = datetime.datetime.fromisoformat(dat['plannedWhen'])
            except: self.departureTime = None
        try: self.departureString = self.departureTime.strftime(humantimeformat)
        except: self.departureString = None

        try:
            self.stopoverStops = []
            for i in range(len(dat['stopovers'])):
                currentStop = Stop(dat['stopovers'][i]['stop']['id'], False)
                self.stopoverStops.insert(i, currentStop)
        except: pass

        try:
            self.departureDelay = int(dat['departureDelay']) / 60
            self.arrivalDelay = int(dat['arrivalDelay']) / 60
            self.delayData: bool = True
        except:
            try:
                self.delay = int(dat['delay']) / 60
                self.delayData: bool = True
            except:
                self.delayData: bool = False
                try: self.delay = int(dat['departureDelay']) / 60
                except: self.delay = 0


        # currentTripPosition
        try:
            self.currentPosition = Location(dat['currentLocation']['latitude'], dat['currentLocation']['longitude'])
        except: self.currentPosition = None

        # Falls gegeben, überprüfe, ob die Fahrt am gegebenen, im Programm geladenen
        # Bahnhof endet, das heißt eine Ankunft besteht
        try:
            if type(loadedStation) == Stop and str(loadedStation.id) == str(self.destination.id):
                self.isArrival = True
            elif type(loadedStation) == Stop and loadedStation.name != self.destination.name:
                self.isArrival = False
            else:
                self.isArrival = None
        except: pass

    def getVia(self, startStopId: str):
        if self.stopoverStops is None or self.stopoverStops == []:
            self.getStopovers()

        # Zu prüfende Stops
        tstops = []
        a = False
        if len(self.stopoverStops) == 0: return []
        for i in self.stopoverStops:
            if a: tstops.append(i)
            if i.stop.id == startStopId:
                a = True

        viastops = []
        for i, e in enumerate(tstops):
            viastops.insert(i, Station(e.stop.id, True))

        highestCategory = 12
        bestStations: Station = None
        for i in viastops:
            if i.category is None: continue
            if i.category < highestCategory and i.id != self.destination.id:
                highestCategory = i.category
                bestStations = i

        return bestStations


    def getStopovers(self):
        url = f'{instance}/trips/{self.tripId}'
        try:
            dat = requests.get(url).json()['trip']
            for i in dat['stopovers']:
                self.stopoverStops.append(TripStop(i))
        except:
            print(f"error while fetching stopovers for trip {self.tripId}")
            return


    def getStopData(self, stopId: str) -> dict:
        inMyStopovers = False
        for i in self.tripData['stopovers']:    # da unten auch anpassen! die stopover-Informationen müssen aus dem tripdata['stopovers'] bezogen werden
            if str(stopId) == str(i['stop']['id']):
                inMyStopovers = True
                return TripStop(i)


        # ^^^^^^^^^^
        # Durchsuche die self.stopoverStops-Liste nach dem Stop, der dem für die Funktion
        # angegegebenen Stop entspricht

        return("error")


class Line:
    def __init__(self, lineData: dict = None):
        # in the transport.rest-api, there's no extra support for lines (yet?, 
        # the hafas-client supports it). The only way to get the data is through
        # the "stops" requests followed by the "linesOfStop" parameter set to true.
        # Because of that, there's no option to fetch the data inside this function.
        self.lineData = lineData
        try:
            self.id = self.lineData['id']
            self.name = self.lineData['name']
            self.productName = self.lineData['productName']
            self.productType = self.lineData['product']
        except:
            print(f"Error: Line {self.id} seems to have corrupt data")
            return


class Station:
    def __init__(self, id: str = None, fetchData = True, data = None):
        if id is None:
            try:
                self.id = data['id']
            except: return

        if data != None:
            self.stationData = data
        elif fetchData == False: return
        if fetchData == True:
            url = f'{instance}/stations/{id}/?language=de'
            self.stationData = requests.get(url).json()

        try:
            d = self.stationData['name']
        except:
            # Fallback für ausländische Stations
            url = f'{instance}/stops/{id}/?language=de'
            self.stationData = requests.get(url).json()

        self.name = self.stationData['name']
        self.id = self.stationData['id']
        self.locationDat = self.stationData['location']
        self.latitude = self.locationDat['latitude']
        self.longitude = self.locationDat['longitude']
        self.hasTripData: bool = False

        try:
            try: self.category = self.stationData['category']
            except: self.category = self.stationData['priceCategory']
        except: self.category = None


class Stop:
    def __init__(self, stopId: str = None, fetchData = True, data = None, fetchLineData: bool = False):

        if stopId == None:
            try:
                self.stopId = data['id']
            except: return

        if data != None:
            self.stopData = data
        elif fetchData == False: return
        if fetchData == True:
            url = f'{instance}/stations/{stopId}/?language=de'
            if fetchLineData == True: url += "&linesOfStops=true"
            self.stopData = requests.get(url).json()

        self.name = self.stopData['name']
        self.id = self.stopData['id']
        self.locationDat = self.stopData['location']
        self.latitude = self.locationDat['latitude']
        self.longitude = self.locationDat['longitude']
        self.hasTripData: bool = False

        try:
            try: self.category = self.stopData['category']
            except: self.category = self.stopData['priceCategory']
        except: self.category = None


        # If given, save the lines
        self.lines = []
        if fetchLineData == True:
            try:
                for i in self.stopData['lines']:
                    self.lines.append(Line(i))
            except: pass
        else: pass
        fetchedStops.append(self)

    def getTrips(self):
        departures = requests.get(f"{instance}/stops/{self.id}/departures{params}").json()
        arrivals = requests.get(f"{instance}/stops/{self.id}/arrivals{params}").json()
        trips = []
        for i in departures['departures']:
            doubled = False
            for y in trips:
                if i['tripId'] == y.tripId: doubled = True
            if not doubled: trips.append(Trip(None, False, self, i, 'departure'))

        for i in arrivals['arrivals']:
            doubled = False
            for y in trips:
                if i['tripId'] == y.tripId: doubled = True
            if not doubled: trips.append(Trip(None, False, self, i, 'arrival'))


        self.trips = sorted(trips, key=lambda x: x.departureString)


class TripStop:
    def __init__(self, tripStopData):
        self.dat = tripStopData
        self.stop = Stop(self.dat['stop']['id'], False, self.dat['stop'])
        self.arrival = None
        self.departure = None
        try:
            try: self.arrival = datetime.datetime.fromisoformat(str(self.dat['arrival'])).strftime(humantimeformat)
            except: self.arrival = datetime.datetime.fromisoformat(str(self.dat['plannedArival'])).strftime(humantimeformat)
        except: pass
        try:
            try: self.departure = datetime.datetime.fromisoformat(str(self.dat['departure'])).strftime(humantimeformat)
            except: self.departure = datetime.datetime.fromisoformat(str(self.dat['plannedDeparture'])).strftime(humantimeformat)
        except: pass

        # AnkunftsGleis
        try: self.arrivalPlatform = self.dat['arrivalPlatform']
        except: self.arrivalPlatform = self.dat['plannedArrivalPlatform']
        if self.dat['arrivalPlatform'] != None and self.dat['arrivalPlatform'] != self.dat['plannedArrivalPlatform']:
            # Falls anderes Gleis als geplant:
            self.arrivalPlatformText = f"""<p><s>{self.dat['plannedArrivalPlatform']}</s> <span style="color:#c0392b"><strong>{self.dat['arrivalPlatform']}</strong></span></p>"""
        else: self.arrivalPlatformText = f'{self.arrivalPlatform}'


        # AbfahrtsGleis
        try: self.departurePlatform = self.dat['departurePlatform']
        except: self.departurePlatform = self.dat['plannedDeparturePlatform']
        if self.dat['departurePlatform'] != None and self.dat['departurePlatform'] != self.dat['plannedDeparturePlatform']:
            # Falls anderes Gleis als geplant:
            self.departurePlatformText = f"""<p><s>{self.dat['plannedDeparturePlatform']}</s> <span style="color:#c0392b"><strong>{self.dat['departurePlatform']}</strong></span></p>"""
        else: self.departurePlatformText = f'{self.departurePlatform}'


fetchedStops = []

def getFetchedStop(stopId) -> Stop:
    success = False
    while not success:
        for i in fetchedStops:
            if str(stopId) == str(i.id):
                success = True
                return i
    return None