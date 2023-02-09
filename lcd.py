import lcddrivers
import time
import datetime
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
display = lcddrivers.Lcd()


def clearDisplay():
    display.lcd_clear()

class Lcdtext:
    def __init__(self, line: int = 1, textLeft: str = "", textMid: str = "", textRight: str = "", runningTextAllowed = True) -> None:
        self.textLeft = textLeft
        self.textMid = textMid
        self.textRight = textRight
        self.line = line
        self.num_cols = 16
        
        doRunningText = False
        if len(self.textLeft) + len(self.textMid) + len(self.textRight) + 2 > self.num_cols and runningTextAllowed:
            doRunningText = True
        else:
            if self.textMid == "":
                self.textMid = " "
                for i in range(self.num_cols-(len(self.textLeft)+len(self.textRight)+3)): self.textMid = self.textMid + " "
            string = ""
            if textLeft: string += textLeft
            if textMid: 
                if textLeft: string += f' {textMid}'
                else: string = textMid
            if textRight:
                if textMid or textLeft: string += f' {textMid}'
                else: string = textRight
            displayString(f'{self.textLeft} {self.textMid} {self.textRight}', self.line)

        if doRunningText:
            self.doRunningText = True
            self.textMid += "   " + self.textMid
            #self.scheduler = BlockingScheduler()
            self.duration = round(len(self.textMid)*0.35)
            self.thread = Thread(target=self.doText)
            self.thread.start()
        else:
            self.doRunningText = False
        
    
    def doText(self):
        while self.doRunningText:
            try:
                textMidLength = self.num_cols - (len(self.textLeft) + len(self.textRight))
                if self.textLeft: textMidLength-=1
                if self.textRight: textMidLength-=1
                for i in range(int(len(self.textMid)/2 + 3)):
                    if self.doRunningText == False: break
                    tTextMid = self.textMid[i:i+textMidLength]
                    displayString(f'{self.textLeft} {tTextMid} {self.textRight}', self.line)
                    time.sleep(0.35)
                time.sleep(2)
            except KeyboardInterrupt: display.lcd_clear()

    def stop(self):
        if self.doRunningText:
            self.doRunningText = False
            self.thread.join()
            del self.thread
        displayString(" " * self.num_cols, self.line)

class Attention:
    def __init__(self, display: lcddrivers.Lcd, times: int = 3, dur: float = 0.3):
        self.display = display
        for i in range(times):
            self.display.lcd_backlight(0)
            time.sleep(dur)
            self.display.lcd_backlight(1)
            time.sleep(dur)

def displayString(string, line):
    print(f"[{line}] {string}")
    try: display.lcd_display_string(string, line)
    except KeyboardInterrupt: display.lcd_clear()

def getDebugTime():
    return datetime.datetime.now().strftime("[%H:%M:%S]")