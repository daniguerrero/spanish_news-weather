#!/usr/bin/python

# Author: Daniel Guerrero
#
# Todo: add some info about what video is playing (date)
# Note that speech is done via festival package
# Had to adapt for festival some words for a better english pronuntation like Lyon=Leeon :-)

from xml.dom import minidom
import urllib
from pprint import pprint
import subprocess
import re
import os


#starting with Lyon
CITY = '609125'
WEATHER_URL = 'http://weather.yahooapis.com/forecastrss?w='+CITY+'&u=c'
WEATHER_NS = 'http://xml.weather.yahoo.com/ns/rss/1.0'

RTVE_URL = 'http://www.rtve.es/rss/temas_telediario-4.xml'
ICON_URL = 'http://l.yimg.com/a/i/us/we/52/'

def weather_for_zip(zip_code):
    url = WEATHER_URL 
    dom = minidom.parse(urllib.urlopen(url))
    forecasts = []
    for node in dom.getElementsByTagNameNS(WEATHER_NS, 'forecast'):
       forecasts.append({
        'date': node.getAttribute('date'),
        'low': node.getAttribute('low'),
        'high': node.getAttribute('high'),
        'condition': node.getAttribute('text')
        })
    ycondition = dom.getElementsByTagNameNS(WEATHER_NS, 'condition')[0]
    return {
        'current_condition': ycondition.getAttribute('text'),
        'current_temp': ycondition.getAttribute('temp'),
        'forecasts': forecasts,
        'icon_code': ycondition.getAttribute('code'),
        'title': dom.getElementsByTagName('title')[2].firstChild.data
    }

def create_speech():
    weather = weather_for_zip(CITY)
    speech = "This is the weather for Leoon, right now we have "+weather['current_condition']+" condition"
    speech += " with a temperature of "+weather['current_temp']+" celsius degrees."
    speech += " The prevision for today is "+weather['forecasts'][0]['condition']+ ", with a minimum temperature of "+weather['forecasts'][0]['low']
    speech += " and a maximum of "+weather['forecasts'][0]['high']+" degrees."
    speech += " Tomorrow is expected to be "+weather['forecasts'][1]['condition']+ ", with a minimum temperature of "+weather['forecasts'][1]['low']
    speech += " and a maximum of "+weather['forecasts'][1]['high']+" degrees."
    #retcode = subprocess.call(["festival", '--tts', '/tmp/workfile'])
    #sent to background so we hear the speech while downloading the video
    os.system('echo '+speech+'| festival --tts&')
    #retcode = subprocess.call(["ls", "-l"])

def find_video():
    url= RTVE_URL
    print 'Analizing: '+url
    dom = minidom.parse(urllib.urlopen(url))
    element = dom.getElementsByTagName('link')[1].firstChild.data
    m = re.search('([0-9]*)\.shtml',element)
    #we keep only the regexp
    s = m.group(1)
    print s
    #converting string to array list
    l = list(s)
    print l
    url2 = 'http://www.rtve.es/swf/data/es/videos/video/'+l[5]+'/'+l[4]+'/'+l[3]+'/'+l[2]+'/'+s+'.xml'
    print 'Analizing: '+url2
    dom = minidom.parse(urllib.urlopen(url2))
    #here we follow instruction on http://www.carballude.es/blog/?p=871 but with python
    try:
       element = dom.getElementsByTagName('file')[0].firstChild.data
       hidden_video = element
    except:
       print "Out of index probably while looking for a file, keep going..."
    element = dom.getElementsByTagName('plugins')[0].getElementsByTagName('plugin')
    for node in element:
       print node.getAttribute('name')
       if node.getAttribute('name') == 'multicdn':
          param = node.getAttribute('params')
    m = re.search('assetDataId::([0-9]*)',param)
    s = m.group(1)
    l = list(s)
    url3 = 'http://www.rtve.es/scd/CONTENTS/ASSET_DATA_VIDEO/'+l[5]+'/'+l[4]+'/'+l[3]+'/'+l[2]+'/'+'ASSET_DATA_VIDEO-'+s+'.xml'
    print 'Analizing: '+url3
    dom = minidom.parse(urllib.urlopen(url3))
    element = dom.getElementsByTagName('fields')[0].getElementsByTagName('field')
    for node in element:
        if node.getElementsByTagName('key')[0].firstChild.data == 'ASD_FILE':
           value = node.getElementsByTagName('value')[0].firstChild.data
    m = re.search('(/flv/.*$)',value)
    s = m.group(1)
    print s
    p = re.search('([0-9]*)\.flv$',s)
    t = p.group(1)
    print t
    hidden_video = 'http://www.rtve.es/resources/TE_NGVA/'+s
    listdir = os.listdir('./')   
    isdown = False
    for file in listdir:
        if os.path.splitext(file)[0] == t:
             print 'The file is already downloaded skiping new downloads...' 
             isdown = True
    if not isdown:  
        print 'Downloading video from url: '+hidden_video
        retcode = subprocess.call(["wget", hidden_video])
    #gathering yahoo data to add weather info on video
    weather = weather_for_zip(CITY)
    ICON_CODE = weather['icon_code']
    url_icon = ICON_URL+ICON_CODE+'.gif'
    print url_icon
    #transforming icon from gif to png
    retcode = subprocess.call(["wget", url_icon])
    retcode = subprocess.call(["gif2png", ICON_CODE+'.gif'])
    os.system('rm *.gif *.gif.*')
    #running vlc with an embedded icon, realtime temperature and hour.
    os.system('export DISPLAY=:0 && /usr/bin/vlc --fullscreen --sub-filter "logo{file='+ICON_CODE+'.png,x=35,y=540,transparency=200}:marq{marquee=%H:%M,x=10,y=10,size=28}:marq{marquee="'\
               +weather['current_temp']+'",x=65,y=543,size=28}" --marq-opacity 200 -I rc '+t+'.flv'+' vlc://quit')
     
def main():
    create_speech()
    find_video()

if __name__ == "__main__":
    main()
