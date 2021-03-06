
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, datetime, buggalo, gzip, StringIO
import simplejson as json

plugin = 'TMZ'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '06-22-2013'
__version__ = '3.0.13'
settings = xbmcaddon.Addon( id = 'plugin.video.tmz' )
dbg = False
dbglevel = 3
icon = os.path.join( settings.getAddonInfo( 'path' ), 'icon.png' )
fanart = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'

import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry

def clean( name ):
	remove = [ ('&amp;','&'), ('&quot;','"'), ('&#39;','\''), ('u2013','-'), ('u201c','\"'), ('u201d','\"'), ('u2019','\''), ('u2026','...') ]
	for trash, crap in remove:
		name = name.replace( trash, crap )
	return name

@retry(IndexError)	
def build_main_directory():
	main=[
		( settings.getLocalizedString( 30007 ), '2' ),
		( settings.getLocalizedString( 30000 ), '0' ),
		( settings.getLocalizedString( 30001 ), '0' ),
		( settings.getLocalizedString( 30002 ), '0' ),
		( settings.getLocalizedString( 30003 ), '0' )
		]
	for name, mode in main:
		u = { 'mode': mode, 'name': name }
		addListItem(label = name, image = icon, url = u, isFolder = True, totalItems = 5, infoLabels = False, fanart = fanart)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("515")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError, ValueError))
def build_video_directory( name ):
	data = getUrl( 'http://www.tmz.com/videos/', True )
	textarea = '[{' + re.compile('{ name: \'' + name.upper() + '\',( )?\n         allInitialJson: {(.+?)},\n         (slug|noPaging)?', re.DOTALL).findall( data )[0][1].replace('\n', '').replace('results:','"results":') + '}]'
	query = json.loads(textarea)[0]["results"]
	totalItems = len(query)
	if settings.getSetting('playall') == 'true':
		playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		playlist.clear()
		u = { 'mode': '4' }
		infoLabels = { "Title": '* ' + settings.getLocalizedString( 30030 ) + ' *', "Plot": settings.getLocalizedString( 30031 ) }
		addListItem('* ' + settings.getLocalizedString( 30030 ) + ' *', icon, u, False, 0, infoLabels, fanart)
	for videos in query:
		title = clean(videos['title'].replace("\\", "")).encode('ascii', 'ignore')
		duration = videos['duration'].replace("\\", "")
		videoUrl = videos['videoUrl'].replace("\\", "")
		thumb = videos['thumbnailUrl'].replace("\\", "") + '/width/490/height/266/type/3'
		try:
			if name == settings.getLocalizedString( 30003 ):
				time = title.rsplit(': ')[1].rsplit(' ')[1].rsplit('/')
				date = '20' + time[2] + '.' + time[0].zfill(2)  + '.' + time[1]
			else:
				date = videos['activeDate'].rsplit('T')[0]
		except:
			date = '0000.00.00'
		if videoUrl.find('http://cdnbakmi.kaltura.com') == -1:
			low_id =  videoUrl.split('_')[0].split('/')[-1:][0] + '_' + videoUrl.split('_')[1]
			high_id = videoUrl.split('_')[0].split('/')[-1:][0] + '_' + videoUrl.split('_')[1] + '/flavorId/0_' + videoUrl.split('_')[3]
		else:
			low_id = videoUrl.split('/')[9]
			high_id = videoUrl.split('/')[9] + '/flavorId/' + videoUrl.split('/')[11]
		if settings.getSetting("quality") == '0':
			url = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/' + low_id
		else:
			url = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/' + high_id
		infoLabels = { "Title": title, "Plot": title, "Duration": str(int(duration)/60), "aired": str(date) }
		u = { 'mode': '1', 'name': title, 'url': url, 'studio': name, 'thumb': thumb }
		addListItem(label = title, image = thumb, url = u, isFolder = False, totalItems = totalItems, infoLabels = infoLabels, fanart = fanart, duration = duration)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, ValueError))	
def build_search_directory():
	page = 1
	checking = True
	string = common.getUserInput(settings.getLocalizedString( 30007 ), "")
	if not string:
		build_main_directory()
		return
	if settings.getSetting('playall') == 'true':
		playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		playlist.clear()
		u = { 'mode': '4' }
		infoLabels = { "Title": '* ' + settings.getLocalizedString( 30030 ) + ' *', "Plot": settings.getLocalizedString( 30031 ) }
		addListItem('* ' + settings.getLocalizedString( 30030 ) + ' *', icon, u, False, 0, infoLabels, fanart)
	while checking:
		url = 'http://www.tmz.com/search/json/videos/' + urllib.quote(string) + '/' + str(page) + '.json'
		data = getPage(url)
		if data['error'] == 'HTTP Error 404: Not Found':
			dialog = xbmcgui.Dialog()
			ok = dialog.ok( plugin , settings.getLocalizedString( 30009 ) + '\n' + settings.getLocalizedString( 30010 ) )
			return
		elif data['error'] != None:
			text = getUrl( url, True )
		else:
			text = data['content']
		jdata = json.loads(text)
		total = int(jdata['total'])
		if ((total - page * 25) > 0):
			page = page + 1
		else:
			checking = False
		for results in jdata['results']:
			title = results['title'].encode('ascii', 'ignore')
			videoUrl = results['URL'].replace("\\", "")
			thumb = results['thumbnailUrl'].replace("\\", "") + '/width/490/height/266/type/3'
			infoLabels = { "Title": title, "Plot": title }
			u = { 'mode': '3', 'name': title, 'url': videoUrl, 'thumb': thumb }
			addListItem(label = title, image = thumb, url = u, isFolder = False, totalItems = total, infoLabels = infoLabels, fanart = fanart)
	xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
	setViewMode("503")
	xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(IndexError)	
def get_search_url(name, url, thumb):
	if settings.getSetting("quality") == '0' or len(url.split('/')[4]) > 10:
		meta = 'http://cdnapi.kaltura.com/p/' + thumb.split('/')[4] + '/sp/' + thumb.split('/')[6] + '/playManifest/entryId/' + thumb.split('/')[9]
		data = getUrl( meta, True )
		url = re.compile('<media url=\"(.+?)\"').findall(data)[0]
	else:
		if len(url.rsplit('-')) == 2: url = url.replace('-', '_')
		data = getUrl( url, True )
		url = common.parseDOM(data, "meta", attrs = { "name": "VideoURL" }, ret = "content")[0]
	play_video( name, url, thumb, settings.getLocalizedString( 30007 ) )

@retry(IndexError)	
def play_video( name, url, thumb, studio ):
	if studio != settings.getLocalizedString( 30007 ):
		try:
			data = getUrl( url, True )
			url = re.compile('<media url=\"(.+?)\"').findall(data)[0]
		except:
			url = 'http://www.tmz.com/videos/' + thumb.split('/')[9]
			data = getUrl( url, True )
			url = common.parseDOM(data, "meta", attrs = { "name": "VideoURL" }, ret = "content")[0]
	infoLabels = { "Title": name , "Studio": "TMZ: " + studio, "Plot": name }
	playListItem(label = name, image = thumb, path = url, infoLabels = infoLabels)
	
def playall():
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	xbmc.Player().play(playlist)
	return

params = getParameters(sys.argv[2])
mode = None
name = None
url = None
studio = None
thumb = None

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:
	name = urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode = int(params["mode"])
except:
	pass
try:
	studio = urllib.unquote_plus(params["studio"])
except:
	pass
try:
	thumb = urllib.unquote_plus(params["thumb"])
except:
	pass

try:
	if mode == None:
		build_main_directory()
	elif mode == 0:
		build_video_directory( name )
	elif mode == 1:
		play_video( name, url, thumb, studio )
	elif mode == 2:
		build_search_directory()
	elif mode == 3:
		get_search_url(name, url, thumb)
	elif mode == 4:
		playall()
except Exception:
	buggalo.onExceptionRaised()
	