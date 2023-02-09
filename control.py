import transport
import lcd
import datetime
import threading
import time

class main:
    def __init__(self, stopId: str = '8002348'):
        self.stop = transport.Stop(stopId)
        self.stop.getTrips()
        lcd.clearDisplay()
        self.line1 = None
        self.line2 = None
        self.thread = threading.Thread(target=self.refresh)
        self.thread.start()

    def refresh(self):
        while True:
            print(f"{getDebugTime()} Refreshing Data...")
            self.stop.getDepartures()

            # alte Daten löschen
            if self.line1:
                self.line1.stop()
                del self.line1 
            if self.line2:
                self.line2.stop()
                del self.line2

                
            self.showTrip(self.stop.departures[0])
            time.sleep(30)
        
        
    def showTrip(self, trip: transport.Trip):
        print(f"{getDebugTime()} Showing Trip to {trip.destinationName}")
        inMinutes = datetime.datetime.fromisoformat(trip.when).replace(tzinfo=None)-datetime.datetime.now()
        print(f' before: {inMinutes}')
        inMinutes = round(inMinutes.seconds / 60)
        print(f' after: {inMinutes}')
        timeText = f"in {inMinutes} Min"
        if inMinutes < 1: timeText = "jetzt"
        
        self.line2 = lcd.Lcdtext(2, timeText, "", f"Gl {trip.platform}", False)
        
        #if self.line1: del self.line1
        self.line1 = lcd.Lcdtext(1, trip.line.shortName, f'nach {trip.destination.name}')
    

def getDebugTime():
    return datetime.datetime.now().strftime("[%H:%M:%S]")


if __name__ == "__main__":
    mainThread = main()