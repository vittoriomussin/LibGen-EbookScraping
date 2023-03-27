from random import sample
import shutil
import sys
from threading import Condition
from queue import Queue
import random
from bs4 import BeautifulSoup
import certifi
from urllib3 import ProxyManager, make_headers
import os
import requests
from selenium import webdriver
import time
import datetime
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
import speedtest

#-----------------------------for webdriver-----------------------------------
import threading
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

#from pyvirtualdisplay import Display
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from fake_useragent import UserAgent

#=====================END IMPORT=============================

threadLock = Condition()
with open("/media/Vittorio/libgen_downloaded.txt", "r") as f:
    scaricati = f.read()

class DownloadThread(threading.Thread):
    def __init__(self, path_csv, archive_csv_path, archive_folder, temp_path, libgen_log):
        threading.Thread.__init__(self)
        #self.lock = Condition()
        self.temp_path = temp_path
        self.path_csv = path_csv
        self.archive_csv_path = archive_csv_path
        self.archive_folder = archive_folder
        self.libgen_log = libgen_log
    
    def download_from_link(self, link, size):
        link = "https://libgen.rocks/ads.php?md5=" + link.split("/")[-1]
        #print(link)
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        #Random window size
        #Sizes = ["1366,768", "3840,2160", "1600,900", "2560,1440", "2560,1600"]
        #size = sample(Sizes,1)[0]
        #options.add_argument(f"--window-size={size}")
        options.add_argument("start-maximized")
        #Random User Agent
        ua = UserAgent()
        userAgent = ua.random
        options.add_argument(f'user-agent={userAgent}')
        options.add_argument("--headless")
        #Setting the default download directory
        preferences = {"download.default_directory": self.temp_path + "/", "download.prompt_for_download" : False, } #download path
        options.add_experimental_option("prefs", preferences)
        #options.add_argument('--no-sandbox')
        #options.add_argument(r'--profile-directory=/home/pi/EbookScraping/Profile 2/')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        #-------------------------------------webdriver initialization------------------------------------------------------
        s=Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=s, options=options)
        #-------------------------------------stealth settings---------------------------------------------------------
        stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True, run_on_insecure_origins = True,)
        #-------------------------------------webdriver actions---------------------------------------------------------           
        driver.get(link)
        time.sleep(random.randint(1, 3) + random.random())
        try:
            bottone = driver.find_element(By.XPATH,'//*[@id="main"]/tbody/tr[1]/td[2]/a') # #//*[@id="download"]/ul/li[1]/a
        except:
            driver.quit()
            return None
        #time.sleep(random.randint(1, 3) + random.random())
        driver.execute_script("arguments[0].click();", bottone)
        #print("bottone premuto")
        if float(size) > 5:
            wifi  = speedtest.Speedtest()
            down = wifi.download()
            quiet = ( float(size) / (down/1000000) ) + 1
            time.sleep(int(quiet))
        else:
            time.sleep(5)
        driver.quit()
        return link
                
    def get_link_from_csv(self):
        threadLock.acquire()
        with open(self.archive_csv_path, "r") as f:
            archive=f.read()
        with open(self.path_csv, "r") as f:
            lines=f.readlines()
        try:
            raw_line=sample(lines, 1)[0]
            line = raw_line.split(";")[0].replace("\n", "")
            size = raw_line.split(";")[1].replace("\n", "")
        except:
            threadLock.release()
            return False
        if line in archive:
            lines.remove(raw_line)
            with open(self.path_csv, "w") as f:
                f.write("".join(lines))
            threadLock.release()
            return False
        else:
            threadLock.release()
            return line, size
        
    def append_archive_csv(self, link):
        with open(self.archive_csv_path, "a") as f:
            f.write(link + "\n")
        
        
    def move_ebook(self):
        name = os.listdir(self.temp_path)[0]
        src_path = self.temp_path + "/" + name 
        dst_path = self.archive_folder + "/" + name
        if os.path.exists(self.archive_folder) == False:
            os.mkdir(self.archive_folder)
        shutil.move(src_path, dst_path)
        return name
        #print("--RUN", time.ctime(), "ebook spostato in", save_dir)
        #os.rmdir(self.temp_path)
        
    
    def setup_temp_path(self):
        ### set temp download directory
        if os.path.exists(self.temp_path) == False:
            os.mkdir(self.temp_path)
        ### remove files if there are
        if len(os.listdir(self.temp_path)) != 0:
            for file_ in os.listdir(self.temp_path):
                os.remove(self.temp_path + "/"+file_)
    
    def write_log(self):
        threadLock.acquire()
        with open(self.libgen_log,"a") as f:
            f.write(self.LOG + "\n")
        threadLock.release()
    
    def libri_scaricati_e_rimanenti(self):
        with open(self.path_csv, "r") as f:
            rimanenti = len(f.readlines())
        scaricati = len(os.listdir(self.archive_folder))
        return "\t libri scaricati: " + str(scaricati) + "\t libri rimanenti: " + str(rimanenti)
    
    def remove_line_from_csv(self, line):
        with open(self.path_csv, "r") as f:
            lines=f.readlines()
        if line in lines:
            lines.remove(line)
            with open(self.path_csv, "w") as f:
                f.write("".join(lines))
        
        
    
    def run(self):
        #i=0
        #scaricati = [i for i in list(os.listdir("/home/pi/EbookScraping/libgen_download_old/")) if ".crdownload" not in i]
        #lista_scaricati = " ".join(scaricati)
        while True:
            try:
                self.LOG = "RUN - " + time.ctime()
                #print("Iterazione: ", i)
                #number_books_0 = len(os.listdir(self.temp_path))
                self.setup_temp_path()
                link, size = self.get_link_from_csv()
                if link==False:
                    continue
                downloaded_link = self.download_from_link(link, size)
                if downloaded_link != None:
                    #number_books_1 = len(os.listdir(self.temp_path))
                    ### check if books have been downloaded
                    if len(os.listdir(self.temp_path))!=0:#number_books_1 > number_books_0:
                        threadLock.acquire()
                        name = self.move_ebook()
                        #--------------------
                        if name in scaricati:
                            threadLock.release()
                            continue
                        #--------------------
                        self.append_archive_csv(link[:-2] +";"+ name)
                        self.remove_line_from_csv(link + ";" + size + "\n")
                        self.LOG+="\t libro scaricato - " + self.temp_path[-2:] + self.libri_scaricati_e_rimanenti()
                        threadLock.release()
                        self.write_log()
                        #print("libro scaricato")
                    else:
                        self.LOG+="\t libro non scaricato - " + self.temp_path 
                        self.write_log()
                        #print("libro non scaricato")
            except Exception as e:
                #self.LOG="ERROR - " + str(e)
                #self.write_log()
                pass

def main_x():
    path_csv = "/media/Vittorio/libgen.txt"
    archive_path_csv = "/media/Vittorio/libgen_archive.txt"
    archive_folder = "/media/Vittorio/libgen_download/"
    temp_path = "/media/Vittorio/libgen_t_"
    libgen_log = "/media/Vittorio/libgen_LOG.txt"
    for i in range(int(sys.argv[1])):
        a = DownloadThread(path_csv, archive_path_csv, archive_folder, temp_path + str(i), libgen_log)
        print("Programma avviato", time.ctime())
        a.start()
    a.join()
    print("Programma terminato", time.ctime())
#if __name__=="__main__":
main_x()
