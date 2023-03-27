import requests
from bs4 import BeautifulSoup
import os
import sys

def main(language = "Italian"):
    csv=""
    link = "https://libgen.is/fiction/?q=&criteria=&language=" + language + "&format=epub&page="
    
    site = requests.get(link+str(1))
    soup = BeautifulSoup(site.text, 'html.parser')
    max_n  = int(soup.find("span", class_ = "page_selector").get_text()[9:])

    if os.path.exists("libgen.txt") == False:
        downloaded = ""
    else:
        with open("libgen.txt", "r") as f:
            downloaded = f.read()
    for n in range(1,max_n+1):
        l= link + str(n)
        site = requests.get(l)
        soup = BeautifulSoup(site.text, 'html.parser')
        for td in soup.find_all("td", text = language):#for a in soup.find_all("a", title="Libgen.rs"):
            size = td.findNext('td').text[7:]
            if "Kb" in size:
                size = int(size[:-2])/1000
            elif "Mb" in size:
                size = float(size[:-3])
            anchor = td.findNext('a').get("href")
            if anchor in downloaded:
                pass
            else:
                csv=anchor + ";" + str(size) + "\n"
                with open("libgen.txt", "a") as f:
                    f.write(csv)
                    
main(language = sys.argv[1])
