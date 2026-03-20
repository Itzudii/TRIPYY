import re
import requests
from bs4 import BeautifulSoup

    
def nonetoO(obj):
    return re.search('0','0').group() if obj is None else obj.group()

def get_coord(string):
    degree = nonetoO(re.search(r"\d+°", string))
    min = nonetoO(re.search(r"\d+.\d+′", string)).replace(degree,'')
    second = nonetoO(re.search(r"\d+.\d+″", string)).replace(min,'')
    return float(re.search(r'\d+',degree).group()) + (float(re.search(r'\d+',min).group())/60) + (float(re.search(r'\d+',second).group())/3600)

def get_coordinates(location):

    url = f'https://en.wikipedia.org/wiki/{location}'
    headers = {'User-Agent': 'MyApp/1.0 (udityasage2004@gmail.com)'}
    response = requests.get(url, headers=headers)
    data = None
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
           latitude =soup.find('span',class_ = 'latitude').text
           longitude =soup.find('span',class_ = 'longitude').text
           data = {'lat' : get_coord(latitude),'lng':get_coord(longitude)}
           return data
        except:
            f'lat and long not found!'
        
        return data if data else None
    else:
        print(f"Error: Unable to retrieve the page. Status code: {response.status_code}")
        return None
