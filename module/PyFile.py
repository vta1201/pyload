#!/usr/bin/env python
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
    @author: mkaay
"""

from module.PullEvents import UpdateEvent
from module.Progress import Progress

from time import sleep
from time import time

statusMap = {
    "finished":    0,
    "offline":     1,
    "online":      2,
    "queued":      3,
    "checking":    4,
    "waiting":     5,
    "reconnected": 6,
    "starting":    7,
    "failed":      8,
    "aborted":     9,
    "decrypting":  10,
    "custom":      11,
    "downloading": 12,
    "processing":  13,
    "unknown":     14
}

def formatSize(size):
    """formats size of bytes"""
    size = int(size)
    steps = 0
    sizes = ["B", "KB", "MB", "GB", "TB"]

    while size > 1000:
        size /= 1024.0
        steps += 1

    return "%.2f %s" % (size, sizes[steps])


class PyFile():
    def __init__(self, manager, id, url, name, size, status, error, pluginname, package, order):
        self.m = manager
        
        self.id = int(id)
        self.url = url
        self.name = name
        self.size = size
        self.status = status
        self.pluginname = pluginname
        self.packageid = package #should not be used, use package() instead
        self.error = error
        self.order = order
        # database information ends here
        
        self.plugin = None
            
        self.waitUntil = 0 # time() + time to wait
        
        # status attributes
        self.active = False #obsolete?
        self.abort = False
        self.reconnected = False
        
        self.progress = Progress()
        if self.status in (0, 4):
            self.progress.setValue(100)
        
        self.progress.notify = self.notifyChange

        self.m.cache[int(id)] = self
        
        
    def __repr__(self):
        return "PyFile %s: %s@%s" % (self.id, self.name, self.pluginname)

    def initPlugin(self):
        """ inits plugin instance """
        if not self.plugin:
            self.pluginmodule = self.m.core.pluginManager.getPlugin(self.pluginname)
            self.pluginclass = getattr(self.pluginmodule, self.pluginname)
            self.plugin = self.pluginclass(self)
    
    
    def package(self):
        """ return package instance"""
        return self.m.getPackage(self.packageid)

    def setStatus(self, status):
        self.status = statusMap[status]
        if self.status in (0, 4):
            self.progress.setValue(100)
        self.sync() #@TODO needed aslong no better job approving exists
    
    def hasStatus(self, status):
        return statusMap[status] == self.status
    
    def sync(self):
        """sync PyFile instance with database"""
        self.m.updateLink(self)

    def release(self):
        """sync and remove from cache"""
        self.sync()
        if hasattr(self, "plugin"):
            del self.plugin
        self.m.releaseLink(self.id)

    def delete(self):
        """delete pyfile from database"""
        self.m.deleteLink(self.id)

    def toDict(self):
        """return dict with all information for interface"""
        return self.toDbDict()

    def toDbDict(self):
        """return data as dict for databse

        format:

        {
            id: {'url': url, 'name': name ... }
        }

        """
        return {
            self.id: {
                'id': self.id,
                'url': self.url,
                'name': self.name,
                'plugin': self.pluginname,
                'size': self.getSize(),
                'format_size': self.formatSize(),
                'status': self.status,
                'statusmsg': self.m.statusMsg[self.status],
                'package': self.packageid,
                'error': self.error,
                'order': self.order,
                'progress': self.progress.getPercent(),
            }
        }
    
    def abortDownload(self):
        """abort pyfile if possible"""
        while self.id in self.m.core.threadManager.processingIds():
            self.abort = True
            if self.plugin and self.plugin.req: self.plugin.req.abort = True
            sleep(0.1)
        
        self.abort = False
        if hasattr(self, "plugin") and self.plugin and self.plugin.req: self.plugin.req.abort = False
        self.release()
        
    def finishIfDone(self):
        """set status to finish and release file if every thread is finished with it"""
        
        if self.id in self.m.core.threadManager.processingIds():
            return False
        
        self.setStatus("finished")
        self.release()
        return True
    
    def formatWait(self):
        """ formats and return wait time in humanreadable format """
        seconds = self.waitUntil - time()
        
        if seconds < 0: return "00:00:00"
                
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
    
    def formatSize(self):
        """ formats size to readable format """
        return formatSize(self.getSize())

    def formatETA(self):
        """ formats eta to readable format """
        seconds = self.getETA()
        
        if seconds < 0: return "00:00:00"
                
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
    
    def getSpeed(self):
        """ calculates speed """
        try:
            return self.plugin.req.get_speed()
        except:
            return 0
        
    def getETA(self):
        """ gets established time of arrival"""
        try:
            return self.plugin.req.get_ETA()
        except:
            return 0
    
    def getBytesLeft(self):
        """ gets bytes left """
        try:
            return self.plugin.req.bytes_left()
        except:
            return 0
    
    def getPercent(self):
        """ get % of download """
        return self.progress.getPercent()
        
    def getSize(self):
        """ get size of download """
        if self.size: return self.size
        else:
            try:
                return self.plugin.req.dl_size
            except:
                return 0
                
    def notifyChange(self):
        e = UpdateEvent("file", self.id, "collector" if not self.package().queue else "queue")
        self.m.core.pullManager.addEvent(e)