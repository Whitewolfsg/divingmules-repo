import urllib
import urllib2
import re
import os
import shutil
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
from BeautifulSoup import BeautifulSoup
from datetime import datetime
import time
try:
    import json
except:
    import simplejson as json
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

addon = xbmcaddon.Addon(id='plugin.video.weather.channel')
addon_version = addon.getAddonInfo('version')
home = xbmc.translatePath(addon.getAddonInfo('path'))
icon = os.path.join( home, 'icon.png' )
fanart = os.path.join( home, 'fanart.jpg' )
cache = StorageServer.StorageServer("weather_channel", 24)
img_dir = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), 'temp_images')
location = addon.getSetting('location')
debug = addon.getSetting('debug')
if debug == 'true':
    cache.dbg = True
ACTION_PREVIOUS_MENU = (9, 10, 92, 216, 247, 257, 275, 61467, 61448)

if location == '':
    if addon.getSetting('first_run') == 'true':
        dialog = xbmcgui.Dialog()
        ok = dialog.yesno('Weather Channel', 'Set a location for local maps and video?')
        if ok:
            addon.openSettings()
            location = addon.getSetting('location')
        addon.setSetting('first_run', 'false')

MAPS = {
    'World - Asia': 'http://www.weather.com/maps/geography/asia/index_large.html',
    'Satellite - World': 'http://www.weather.com/maps/maptype/satelliteworld/index_large.html',
    'World - Polar': 'http://www.weather.com/maps/geography/polar/index_large.html',
    'World - Australia': 'http://www.weather.com/maps/geography/australia/index_large.html',
    'US Regions - Current': 'http://www.weather.com/maps/maptype/currentweatherusregional/index_large.html',
    'US Regions - Southwest': 'http://www.weather.com/maps/geography/southwestus/index_large.html',
    'World - South America': 'http://www.weather.com/maps/geography/southamerica/index_large.html',
    'US Regions - West ': 'http://www.weather.com/maps/geography/westus/index_large.html',
    'Short Term Forecast': 'http://www.weather.com/maps/maptype/forecastsusnational/index_large.html',
    'World - North America': 'http://www.weather.com/maps/geography/northamerica/index_large.html',
    'World - Europe': 'http://www.weather.com/maps/geography/europe/index_large.html',
    'World - Pacific': 'http://www.weather.com/maps/geography/pacific/index_large.html',
    'World - Africa & Mid East': 'http://www.weather.com/maps/geography/africaandmiddleeast/index_large.html',
    'Doppler Radar': 'http://www.weather.com/maps/maptype/dopplerradarusnational/index_large.html',
    'Satellite - US': 'http://www.weather.com/maps/maptype/satelliteusnational/index_large.html',
    'US Regions - East Central': 'http://www.weather.com/maps/geography/eastcentralus/index_large.html',
    'US Regions - Southeast': 'http://www.weather.com/maps/geography/southeastus/index_large.html',
    'Hawaii': 'http://www.weather.com/maps/geography/hawaiius/index_large.html',
    'Alaska': 'http://www.weather.com/maps/geography/alaskaus/index_large.html',
    'US Regions - South Central': 'http://www.weather.com/maps/geography/southcentralus/index_large.html',
    'Severe Alerts - US': 'http://www.weather.com/maps/maptype/severeusnational/index_large.html',
    'Weekly Planner': 'http://www.weather.com/maps/maptype/weeklyplannerusnational/index_large.html',
    'US Regions - Midwest': 'http://www.weather.com/maps/geography/midwestus/index_large.html',
    'US Regions - Central': 'http://www.weather.com/maps/geography/centralus/index_large.html',
    'US Regions - North Central': 'http://www.weather.com/maps/geography/northcentralus/index_large.html',
    'Severe Alerts - Regional': 'http://www.weather.com/maps/maptype/severeusregional/index_large.html',
    'World - Central America': 'http://www.weather.com/maps/geography/centralamerica/index_large.html',
    'Extended Forecasts': 'http://www.weather.com/maps/maptype/tendayforecastusnational/index_large.html',
    'US Regions - Northwest': 'http://www.weather.com/maps/geography/northwestus/index_large.html',
    'US Regions - Forecasts': 'http://www.weather.com/maps/maptype/forecastsusregional/index_large.html',
    'Current Weather': 'http://www.weather.com/maps/maptype/currentweatherusnational/index_large.html',
    'US Regions - Northeast': 'http://www.weather.com/maps/geography/northeastus/index_large.html',
    'US Regions - West Central': 'http://www.weather.com/maps/geography/westcentralus/index_large.html'
    }


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.weather.channel-%s]: %s" %(addon_version, string))


def make_request(url, info=False):
        addon_log('Request URL: ' + url)
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                       'Referer' : 'http://www.weather.com'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response_info = response.info()
            response.close()
            if info:
                try:
                    return(data, response_info['expires'])
                except KeyError:
                    return(data, 'none')
            else: return data
        except urllib2.URLError, e:
            addon_log('We failed to open "%s".' % url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: %s' %e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' % e.code)


def get_local_data(location_name=False, first_run=0):
        p_dialog = xbmcgui.DialogProgress()
        p_dialog.create('Weather Channel', 'Updating Local Data')
        if not location_name:
            url = 'http://xoap.weather.com/search/search?where=%s' %urllib2.quote(location)
        else:
            url = 'http://xoap.weather.com/search/search?where=%s' %urllib2.quote(location_name)
        addon_log('--- get local data url: %s ---' %url)
        soup = BeautifulSoup(make_request(url))
        wc_id = None
        l_data = soup('loc')
        if l_data:
            for i in l_data:
                if i['type'] == '1': wc_id = i['id']
                else: location_name = i.string.split('(')[0]
            if wc_id is None:
                if first_run == 0:
                    if location_name:
                        return get_local_data(location_name, 1)
        else:
            addon_log('unable to determin location')
            cache.set("local_data", repr({ "location": location, "wc_id": '' }))
            p_dialog.close()
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Weather Channel', 'Unable to determine location.\n Try different terms for the location setting.')
            return False

        addon_log('cache local data: %s ' %(location+" - "+wc_id))

        url = 'http://www.weather.com/weather/map/classic/%s' %wc_id
        soup = BeautifulSoup(make_request(url))
        maps = []
        for i in soup('option'):
            if not i['value'] == '':
                maps.append((i['value'], i.string))
        videos = []
        for i in soup('a', attrs={'id' : 'lid2'}):
            href = i['href']
            name = i.string
            videos.append((href, name))
        cache.set("local_data", repr({"location": location, "wc_id": wc_id, "videos": json.dumps(videos), "maps": json.dumps(maps)}))
        p_dialog.close()
        return True


def get_maps(map_cache=False):
        if map_cache:
            for i in json.loads(eval(cache.get("local_data"))['maps']):
                addMapDir(i[1], i[0])

        for i in MAPS.keys():
            addMapDir(i, MAPS[i])


def cache_categories():
        url = 'http://www.weather.com/video'
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        playlist_menu = soup.find('ul', attrs={'class': "ve-playlist_menu ve-js-playlist-menu"})
        page_cats = {}
        for i in playlist_menu('h3'):
            items = i.findNext('ul')('a')
            page_cats[i.string] = []
            for item in items:
                page_cats[i.string].append((item.string, item['href']))
        return page_cats


def categories():
        try:
            if eval(cache.get("local_data"))['wc_id'] != '':
                for i in json.loads(eval(cache.get("local_data"))['videos']):
                    addLink(i[1], i[0], '', '', icon,6)
        except: pass
        addDir('Weather Maps','',4,icon)
        cats = cache.cacheFunction(cache_categories)
        for i in cats.keys():
            addDir(i, '', 1, icon)


def get_subcate(name):
        cats = cache.cacheFunction(cache_categories)
        items = cats[name]
        for i in items:
            cat_id = i[1].split('collid=')[1]
            addDir(i[0], cat_id, 2, icon)


def index(url, play=False):
        if not url.startswith('http://'):
            url = 'http://www.weather.com/data/video?cmd=collection&id=%s' %url
            url += '&chunk=0%3A12'
        page = make_request(url)
        data = json.loads(page.replace('\n','').replace('\t','').strip()[1:-2])
        addon_log('Total Items: '+data['collSize'])
        addon_log('Start Index: '+str(int(data['chunkSize']) * int(data['chunkIndex'])))
        found = False
        for i in data['clips']:
            title = i['title']
            try: thumb = i['largethumb']
            except: thumb = i['thumb']
            desc = i['description']
            vid_url = i['video_source']
            date = i['context']
            if play:
                if play in i['URL']:
                    found = True
                    item = xbmcgui.ListItem(path=vid_url)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                    break
            else:
                addLink(title,vid_url,date,desc,thumb,8)

        if play:
            if not found:
                addon_log('NOT FOUND')
                if int(data['collSize']) >= (int(data['chunkSize']) * (int(data['chunkIndex'])+1)):
                    url = url.split('chunk=')[0]
                    url += 'chunk='+str(int(data['chunkIndex']) + 1)+'%3A12'
                    addon_log('ReTry: '+url)
                    index(url, play)

        elif int(data['collSize']) >= (int(data['chunkSize']) * (int(data['chunkIndex'])+1)):
            url = url.split('chunk=')[0]
            url += 'chunk='+str(int(data['chunkIndex']) + 1)+'%3A12'
            addDir('Next Page', url, 2, icon)


def get_local_video(url):
        url = 'http://www.weather.com'+url
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        container = soup.find('div', attrs={'class': "ve-playlist_content ve-js-clipcontent-container"})
        href = container('div', attrs={'class': "ve-playlist_clip-labels"})[0].a['href']
        cat_id = href.split('collid=')[1]
        addon_log("INDEX: %s, %s" %(cat_id, url.split('/')[-1]))
        index(cat_id, url.split('/')[-1])


def get_images(url, name):
        if url.startswith('/maps'):
            url = 'http://www.weather.com%s' %url
        elif not url.startswith('http://'):
            url = 'http://www.weather.com/weather/map/classic/%s?mapdest=%s' %(eval(cache.get('local_data'))['wc_id'], url)
        addon_log('Map URL: ' + url)
        soup = BeautifulSoup(make_request(url))
        image_urls = []
        try:
            mapregion = soup('a', attrs={'showanimation' : 'yes'})[0]['mapregion']
            for i in range(1, 6):
                image_urls.append('http://image.weather.com/looper/archive/%s/%dL.jpg ' %(mapregion, i))
        except:
            addon_log('No animation')
            try:
                image_urls.append(soup('img', attrs={'name' : 'mapImg'})[0]['src'])
            except:
                addon_log('img_url error')
                return
        addon_log('Images: %s' %len(image_urls))
        images = None
        if len(image_urls) > 0:
            name = 'Map_'+name.replace(':','').replace(' ','_')
            try:
                img_info = eval(cache.get(name))[name]
            except:
                addon_log('img_info exception')
                images = download_images(image_urls, name)
                img_info = eval(cache.get(name))[name]

            expired = False
            for i in img_info['info'].values():
                if i == 'none':
                    expired = True
                elif datetime.utcnow() > datetime.fromtimestamp(time.mktime(time.strptime(i, '%a, %d %b %Y %H:%M:%S GMT'))):
                    expired = True
                    addon_log('Expired: %s' %datetime.fromtimestamp(time.mktime(time.strptime(i, '%a, %d %b %Y %H:%M:%S GMT'))))
                    addon_log('UTC-Now: %s' %datetime.utcnow())
                    break
            if expired:
                images = download_images(image_urls, name)
            else:
                images = img_info['urls']

            w = GUI('image_testing.xml', home, images=images)
            w.doModal()
            del w
        else:
            addon_log('No Images Were Found')


def download_images(images, name):
        p_dialog = xbmcgui.DialogProgress()
        p_dialog.create('Weather Channel', 'Updating Images')
        if not xbmcvfs.exists(img_dir):
            xbmcvfs.mkdir(img_dir)
        image_dir = os.path.join(img_dir, name)
        if not xbmcvfs.exists(image_dir):
            xbmcvfs.mkdir(image_dir)
        else:
            try:
                for i in xbmcvfs.listdir(image_dir)[1]:
                    xbmcvfs.delete(os.path.join(image_dir, i))
            except AttributeError:
                shutil.rmtree(image_dir)
                xbmcvfs.mkdir(image_dir)
        img_info = {}
        img_urls = []
        percent = 0
        for i in range(len(images)):
            data = make_request(images[i], True)
            img_info[images[i]] = data[1]
            if not data[1] == 'none':
                dt = datetime.fromtimestamp(time.mktime(time.strptime(data[1], '%a, %d %b %Y %H:%M:%S GMT')))
                img_name = str(i)+"_"+datetime.strftime(dt, '%H_%M_%S')+images[i].split('/')[-1]
            else:img_name = str(i)+"_"+datetime.strftime(datetime.utcnow(), '%H_%M_%S')+images[i].split('/')[-1]
            img_file = xbmc.translatePath(os.path.join(image_dir, img_name))
            img_urls.append(img_file)
            addon_log('Saving Image: %s' %img_name)
            f = open(img_file, 'wb')
            f.write(data[0])
            f.close
            if len(images) > 1:
                percent += 20
            p_dialog.update(percent)
        cache.set(name, repr({ name: { 'info': img_info, 'urls': img_urls }}))
        xbmc.sleep(500)
        p_dialog.close()
        return img_urls



class GUI(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.images = kwargs.get( "images" )

    def onInit(self):
        self.img = self.getControl(100)
        while xbmc.getCondVisibility('Window.IsActive(13000)') == 1:
            for i in range(len(self.images)):
                self.img.setImage(self.images[i])
                if i == (len(self.images)-1):
                    xbmc.sleep(5000)
                else:
                    xbmc.sleep(700)

    def onAction(self, action):
        # Same as normal python Windows.
        if action in ACTION_PREVIOUS_MENU:
            self.close()

    def onClick(self, controlID):
        """
            Notice: onClick not onControl
            Notice: it gives the ID of the control not the control object
        """
        pass

    def onFocus(self, controlID):
        pass


def clear_cache():
        try:
            cache.delete("local_d%")
        except:
            addon_log('clear_cache exception local_data')
        try:
            cache.delete("Map_%")
        except:
            addon_log('clear_cache exception Map')


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


def addLink(name,url,date,description,iconimage,mode):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":description } )
        liz.setProperty("Fanart_Image", fanart)
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setProperty("Fanart_Image", fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def addMapDir(name, url):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=5&name="+urllib.quote_plus(name)
        liz=xbmcgui.ListItem(name, iconImage="icon", thumbnailImage=icon)
        liz.setInfo(type="Picture", infoLabels={ "Title": name})
        liz.setProperty("Fanart_Image", fanart)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)


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

addon_log("Mode: "+str(mode))
addon_log("URL: "+str(url))
addon_log("Name: "+str(name))

if mode==None:
    if not location == '':
        addon_log('Location: %s' %location)
        try:
            l_cache = eval(cache.get('local_data'))['location']
        except:
            l_cache = ''
        addon_log('cached location: %s' %l_cache)
        # check if location is set or has changed
        if (len(l_cache) == 0) or (not location == l_cache):
            if get_local_data():
                # give storageserver a moment to finish
                xbmc.sleep(1000)
                addon_log('updated local information: %s' %eval(cache.get('local_data'))['location'])
            else:
                addon_log('Unable to get local data!')
                addon.setSetting('location', '')
    categories()

elif mode==1:
    get_subcate(name)

elif mode==2:
    index(url)

elif mode==3:
    play_latest()

elif mode==4:
    try:
        # this will error on first run ??
        if eval(cache.get('local_data'))['wc_id'] != '':
            get_maps(True)
        else:
            get_maps()
    except:
        get_maps()

elif mode==5:
    get_images(url, name)

elif mode==6:
    get_local_video(url)

elif mode==7:
    clear_cache()

elif mode==8:
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
