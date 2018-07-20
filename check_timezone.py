import datetime
import time
from datetime import datetime

today = datetime.now()
gmttime = time.strftime("%d %b %Y %H:%M:%S %Z", time.gmtime())
localtime = time.strftime("%d %b %Y %H:%M:%S %Z", time.localtime())

gmtime2 = time.gmtime()
loctime = time.localtime()

print('GMTTIME: ' + str(gmttime))
print('LOCALTIME: ' + str(localtime))
print('CURRENTTIME: ' + today.strftime("%a, %d %b %Y %H:%M:%S %Z"))
print('UTCNOW: ' +  str(datetime.utcnow()))
print('TIMEZONE: ' + str(loctime.tm_hour - gmtime2.tm_hour))
