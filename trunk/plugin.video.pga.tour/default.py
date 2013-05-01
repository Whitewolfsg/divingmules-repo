import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import StorageServer
from BeautifulSoup import BeautifulSoup
try:
    import json
except:
    import simplejson as json
from subprocess import Popen, PIPE, STDOUT

addon = xbmcaddon.Addon(id='plugin.video.pga.tour')
home = xbmc.translatePath(addon.getAddonInfo('path'))
icon = os.path.join( home, 'icon.png' )
fanart = os.path.join( home, 'fanart.jpg' )
fanart1 = os.path.join( home, 'resources/fanart1.jpg' )
cache = StorageServer.StorageServer("pgatour", 24)
cache.dbg = True

def make_request(url):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
                   'Referer' : 'http://www.pgatour.com'}
        try:
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
                
                
def get_homepage(url):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        homepage = {}
        latest_videos = []
        items = soup.find('div', attrs={'id': 'latest'}).ul('li')
        for i in items:
            href = i.a['href']
            thumb = i.img['src']
            title = i('span', attrs={'class': 'tourVidLatestPodTile'})[0].string
            latest_videos.append((title, href, thumb))
        homepage['latest_videos'] = latest_videos

        categories = []
        items = soup.find('div', attrs={'id': "tourVideoCategories"})('a')
        for i in items:
            href = i['href']
            title = i.string
            categories.append((title, href))
        homepage['categories'] = categories
        return homepage
        
        
def cache_pgatour():
        return get_homepage('http://www.pgatour.com/video.html')
        
def cache_championstour():
        return get_homepage('http://www.pgatour.com/champions/video.html')
        
def cache_webtour():
        return get_homepage('http://www.pgatour.com/webcom/video.html')

def categories():
        addDir('PGA Tour','cache_pgatour',1,icon)
        addDir('Champions Tour','cache_championstour',1,icon)
        addDir('WEB.com Tour','cache_webtour',1,icon)
        
        
def subcategories(url):
        addDir('Latest Videos', url, 3, icon)
        cats = cache.cacheFunction(eval(url))
        for i in cats['categories']:
            addDir(i[0].title(), i[1], 2, icon)
            
            
def get_channels(url):
        json_url = 'http://www.pgatour.com/content/pgatour/video/jcr:content/mediaGallery.media.json?start=0&'
        pattern = "javascript:searchByTags\('(.+?)','(.+?)'\)"
        for tourId, catId in re.findall(pattern, url):
            tourId = urllib.quote(tourId, safe='')
            catId = urllib.quote(catId, safe='')
            json_url += 'tourTagId=%s&categoryTagId=%s' %(tourId, catId)
        data = json.loads(make_request(json_url))
        for i in data['franchise']:
            name = i['name']
            chanId = i['id']
            current = i['current']
            chanUrl = json_url+'&channelTagId='+urllib.quote(chanId, safe='')
            addDir(name, chanUrl, 3, icon)
            

def latest_videos(url):
        tour = cache.cacheFunction(eval(url))
        for i in tour['latest_videos']:
            addLink(i[0].encode('utf-8'), i[1], '', i[2], '')
            
            
def get_video(url):
        data = make_request('http://www.pgatour.com/content/pgatour'+url)
        pattern = "var videoPlayer = OO.Player.create\('.+?','(.+?)',"
        try: video_id = re.findall(pattern, data)[0]
        except:
            print 'Did not find video ID'
            return
        manifest_url = 'http://pgaondemand-a.akamaihd.net/%s/%s_1.f4m' %(video_id, video_id)
        print 'Manifest URL: '+manifest_url
        target = 'php %s' %os.path.join(home, 'resources', 'AdobeHDS.php')
        target += ' --manifest %s --delete --outdir %s --outfile pga.flv' %(manifest_url, os.path.join(home, 'resources'))
        log = open(os.path.join(home, 'resources', 'AdobeHDS.log'), 'w')
        p = Popen(target, shell=True, stdout=log, bufsize=-1)
        p_dialog = xbmcgui.DialogProgress()
        p_dialog.create('Getting Video', 'Please Wait')
        play_file = os.path.join(home, 'resources', 'pga.flv')
        xbmc.sleep(5000)
        percent = 0
        for i in range(10):
            percent += 10
            p_dialog.update(percent)
            success = xbmcvfs.exists(play_file)
            if success:
                p_dialog.close()
                xbmc.Player().play(play_file)
                play_check(play_file)
                break
            else:
                print 'Sleeping 5 seconds'
                xbmc.sleep(5000)
        if not success:
            p_dialog.close()
        
        
def play_check(play_file):
        while (True):
            play_file == get_file()
            xbmc.sleep(1000)
            if play_file != get_file():
                print 'Breaking Loop!'
                os.remove(play_file)
                break

def get_file():
        try:
            file_name = xbmc.Player().getPlayingFile()
        except:
            file_name = None
        return file_name
        
        
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param


def addLink(name,url,desc,thumb,duration):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=4&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot":desc, "Duration":duration} )
        liz.setProperty( "Fanart_Image", fanart1 )
        # liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def addPlaylist(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok        
        
              
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
        print ""
        categories()
        
if mode==1:
        print ""
        subcategories(url)

if mode==2:
        print ""
        get_channels(url)
        
if mode==3:
        print ""
        latest_videos(url)
        
if mode==4:
        print ""
        get_video(url)
        
if mode==5:
        print ""
        getVideos(url)
        
if mode==6:
        print ""
        playLatest()
        

xbmcplugin.endOfDirectory(int(sys.argv[1]))