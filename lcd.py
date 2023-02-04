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
        self.text=text
        #self.scheduler.add_job(self.long_string, 'interval', seconds=1, id="text")
        self.scheduler = BackgroundScheduler()
        self.duration = int((len(self.text)-16)*0.40)+3
        print(self.duration)
        self.scheduler.add_job(self.long_string, 'interval', seconds=self.duration)
        self.long_string()
        self.scheduler.start()
        


    def long_string(self):
        """ 
        Parameters: (driver, string to print, number of line to print, number of columns of your display)
        Return: This function send to display your scrolling string.
        """
        num_line=1
        num_cols=16
        if len(self.text) > num_cols:
            display.lcd_display_string(self.text[:num_cols], num_line)
            for i in range(len(self.text) - num_cols + 1):
                text_to_print = self.text[i:i+num_cols]
                display.lcd_display_string(text_to_print, num_line)
                time.sleep(0.4)
        
        else:
            display.lcd_display_string(self.text, num_line)



    
    def stop(self):
        self.scheduler.remove_job("text")



infotext_sers = Lcdtext("Hallo")

while True:
    time.sleep(1)
