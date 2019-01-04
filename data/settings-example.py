#characters that the file system doesn't allow in a filename or that might confuse the Kodi scrapper
illegalchars = '<>:"/\|?* '

#what to use to replace illegal characters
illegalreplace = '.'

#what to use to replace trailing periods in a name (problem for folders on Windows)
endreplace = ''

#the date format for the season date (default matches thetvdb.com)
dateformat = '%Y-%m-%d'

#the default title of the Kodi dialog box
title = 'Available Streaming'

#the default message in the Kodi dialog box
msg = 'This video is available from a streaming service on another device'

#the root of the video source for Kodi (minus the TV Show and Movie directories)
#note that for Windows you need to put the path in the C:\\Users\\Public\\Videos'
rootpath = None

#the name of the directory where the TV Shows are stored
tvroot = 'TV'

#the name of the directory where Movies are stored
movieroot = 'Movies'

#if another instance of script is running, amount of time (in seconds) to wait before giving up
aborttime = 30

#number of script logs to keep
logbackups = 1

#for debugging you can get a more verbose log by setting this to True
debug = False