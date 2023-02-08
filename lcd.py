import drivers
import time
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

display = drivers.Lcd()

def sers():
    print("sers")



class Lcdtext:
    def __init__(self, text:str) -> None:
        self.dotext=True
        #line 1 of the LCD Display
        self.textLeft ="Train Line"
        self.textMid = "destination"
        self.text = self.textMid
        #line 2 of the LCD Display
        self.textLeftBottom = "when"
        self.textRightBottom = "platform_number"
        #self.scheduler.add_job(self.long_string, 'interval', seconds=1, id="text")
        self.scheduler = BackgroundScheduler()
        self.firstLineScrollTextMaxLength = 16 - (len(self.textLeft) + 1)
        print(self.firstLineScrollTextMaxLength)
        self.duration = int((len(self.text) - self.firstLineScrollTextMaxLength) * 0.40) + 3
        print(self.duration)
        self.scheduler.add_job(self.long_string, 'interval', seconds=self.duration)
        self.long_string()
        self.scheduler.start()
        #Background job for Line 2, for example platform and when the train arrives
        self.scheduler2 = BackgroundScheduler()
        self.scheduler2.add_job(self.statusline2, id="statusline2")
        self.statusline2()
        self.scheduler2.start()



    def long_string(self):
        
        self.destinationTripCharacterLength = len(self.textMid)
        if (len(self.textMid) > self.firstLineScrollTextMaxLength):
            num_line=1
            num_cols=self.firstLineScrollTextMaxLength
            if len(self.text) > self.firstLineScrollTextMaxLength:
                display.lcd_display_string(self.text[:num_cols], num_line)
                for i in range(len(self.text)   - num_cols + 1):
                    text_to_print = self.text[i:i+num_cols]
                    self.firstLine = f'{self.textLeft} {text_to_print}'
                    display.lcd_display_string(self.firstLine, 1)
                    time.sleep(0.4)
            
        if (self.destinationTripCharacterLength < 11):
                display.lcd_display_string(f'{self.textLeft} {self.textMid}', 1)

    
    def stop(self):
        self.scheduler.remove_job("text")
    def statusline2(self):
        self.statusStringTest = self.textLeftBottom
        self.statusLine2Length = len(self.textLeftBottom) + len(self.textRightBottom)
        print(self.statusLine2Length)
        self.remainingSpace = 16 - self.statusLine2Length + len(self.textLeftBottom)
        self.statusStringFinal = f'{self.textLeftBottom.ljust(self.remainingSpace)}{self.textRightBottom}'
        display.lcd_display_string(self.statusStringFinal, 2)
        
    def stopstatusline2(self):
        self.scheduler2.remove_job("statusline2")
infotext_sers = Lcdtext("")

while True:
    time.sleep(1)
