import os
from Renderer import Renderer
from enigma import ePixmap
from Tools.Directories import pathExists, SCOPE_SKIN_IMAGE, SCOPE_CURRENT_SKIN, resolveFilename
from Components.Harddisk import harddiskmanager

searchPaths = []
lastLcdPiconPath = None

def initLcdPiconPaths():
	global searchPaths
	searchPaths = []
	for mp in ('/usr/share/enigma2/', '/'):
		onMountpointAdded(mp)
	for part in harddiskmanager.getMountedPartitions():
		onMountpointAdded(part.mountpoint)

def onMountpointAdded(mountpoint):
	global searchPaths
	try:
		path = os.path.join(mountpoint, 'lcd_picon') + '/'
		if os.path.isdir(path) and path not in searchPaths:
			for fn in os.listdir(path):
				if fn.endswith('.png'):
					print "[LcdPicon] adding path:", path
					searchPaths.append(path)
					break
	except Exception, ex:
		print "[LcdPicon] Failed to investigate %s:" % mountpoint, ex

def onMountpointRemoved(mountpoint):
	global searchPaths
	path = os.path.join(mountpoint, 'lcd_picon') + '/'
	try:
		searchPaths.remove(path)
		print "[LcdPicon] removed path:", path
	except:
		pass

def onPartitionChange(why, part):
	if why == 'add':
		onMountpointAdded(part.mountpoint)
	elif why == 'remove':
		onMountpointRemoved(part.mountpoint)

def findLcdPicon(serviceName):
	global lastLcdPiconPath
	if lastLcdPiconPath is not None:
		pngname = lastLcdPiconPath + serviceName + ".png"
		if pathExists(pngname):
			return pngname
	global searchPaths
	for path in searchPaths:
		if pathExists(path):
			pngname = path + serviceName + ".png"
			if pathExists(pngname):
				lastLcdPiconPath = path
				return pngname
	return ""

def getLcdPiconName(serviceName):
	#remove the path and name fields, and replace ':' by '_'
	sname = '_'.join(serviceName.split(':', 10)[:10])
	pngname = findLcdPicon(sname)
	if not pngname:
		fields = sname.split('_', 3)
		if len(fields) > 2 and fields[2] != '2':
			#fallback to 1 for tv services with nonstandard servicetypes
			fields[2] = '1'
			pngname = findLcdPicon('_'.join(fields))
	return pngname

class LcdPicon(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.pngname = ""
		self.lastPath = None
		pngname = findLcdPicon("lcd_picon_default")
		self.defaultpngname = None
		if not pngname:
			tmp = resolveFilename(SCOPE_CURRENT_SKIN, "lcd_picon_default.png")
			if pathExists(tmp):
				pngname = tmp
			else:
				pngname = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/lcd_picon_default.png")
		if os.path.getsize(pngname):
			self.defaultpngname = pngname

	def addPath(self, value):
		if pathExists(value):
			global searchPaths
			if not value.endswith('/'):
				value += '/'
			if value not in searchPaths:
				searchPaths.append(value)

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				self.addPath(value)
				attribs.remove((attrib,value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def changed(self, what):
		if self.instance:
			pngname = ""
			if what[0] != self.CHANGED_CLEAR:
				pngname = getLcdPiconName(self.source.text)
			if not pngname: # no lcd_picon for service found
				pngname = self.defaultpngname
			if self.pngname != pngname:
				if pngname:
					self.instance.setScale(1)
					self.instance.setPixmapFromFile(pngname)
					self.instance.show()
				else:
					self.instance.hide()
				self.pngname = pngname

harddiskmanager.on_partition_list_change.append(onPartitionChange)
initLcdPiconPaths()
