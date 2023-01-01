# create.kodi.mediastubs
This script generates a set of text files you can use in Kodi for TV shows or movies that are on Bluray discs (or some other outside source like a streaming service).

## PREREQUISITES:
Python 3.x (tested with Python 3.7).  This almost certainly won't work with Python 2.7 (or earlier).  Please see <https://legacy.python.org/dev/peps/pep-0373/> for information on the sunset date for Python 2.7.

### Other Modules
There in one other module that is required for the script to work properly.
```
pip3 install requests
```

## INSTALLATION:
To install download and unzip in any directory.

## CONFIGURATION
The script will run with no configuration. Just be aware that if you don't at least set a root directory that all folders and files created will be in the data directory of the addons.  TV shows will be in a directory called TVShows, and movies will be in a directory called Movies.  If you want to add any configuration options, create a file called settings.py and place it in the data directory of the script. Here are the available options:


* `illegalchars = '<string>'` (default `'<>:"/\|?* '`)  
Characters that the file system doesn't allow in a filename or that might confuse the Kodi scrapper.

* `illegalreplace = '<string>'` (default `'.'`)  
What character to use to replace illegal characters.

* `endreplace = '<string>'` (default `''`)  
What character to use to replace trailing periods in a name (problem for folders on Windows).

* `dateformat = '<string>'` (default `'%Y-%m-%d'`)  
The date format for the season date used by the command line and the settings file.

* `tvmaze_user = '<string>'` (default `''`)  
For functions requiring a TVMaze subscription, the TVMaze user name.

* `tvmaze_apikey = '<string>'` (default `''`)  
For functions requiring a TVMaze subscription, the TVMaze api key.

* `tvmaze_wait = '<string>'` (default `'0.12'`)  
Amount of time (in secs) to wait between calls to TVMaze (to stay under API limiting).

* `title = '<string>'` (default `'Available Streaming'`)  
The default title of the Kodi dialog box.

* `msg = '<string>'` (default `'This video is available from a streaming service on another device'`)  
The default message in the Kodi dialog box. If you are using TV Maze tags, you can set this to `'tag-based'` and the script will create a unique message for each tag group.

* `rootpath = '<string>'` (default `''`)  
The root of the video source for Kodi (minus the TV Show and Movie directories).  The directory path needs to be noted in POSIX format (i.e. `/this/is/the/path`) and start at the root directory for the file system.  For Windows include the drive letter as the first directory (i.e. `/C:/this/is/the/path`).

* `tvroot = '<string>'` (default `'TVShows'`)  
The name of the directory where the TV shows are stored.

* `movieroot = '<string>'` (default `'Movies'`)  
The name of the directory where movies are stored.

* `videos = <list> of <dicts>` (default `[]`)  
If you set this setting, you can run the script daily and have in generate new strm or media stub files based on a schedule. More on that in usage below.

* `aborttime = <int>` (default `30`)  
If another instance of script is running, amount of time (in seconds) to wait before giving up.

* `logbackups = <int>` (default `7`)
The number of days of logs to keep.

* `debug = <boolean>` (default `False`)
For debugging you can get a more verbose log by setting this to True.

## USAGE

```
usage: execute.py [-h] (-n NAME | -f SOURCE) [-i TVMAZEIDS] [-l LOOKBACK]
                  [-s SEASONS] [-e EPISODES] [-d DATES] [-t TITLE] [-m MSG]
                  [-y TYPE] [-u TVMAZE_USER] [-a TVMAZE_APIKEY] [-r]

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  the name of the series/movie
  -f SOURCE, --source SOURCE
                        generate file based on either 'settings' or 'tvmaze'
  -i TVMAZEIDS, --tvmazeids TVMAZEIDS
                        TV Maze IDs (comma sep), 'followed', or 'tags:tagids' (comma sep)
  -l LOOKBACK, --lookback LOOKBACK
                        number of days backwards in time to look for episode match
  -s SEASONS, --seasons SEASONS
                        comma separated list of the seasons to create
  -e EPISODES, --episodes EPISODES
                        comma separated list of the number of episodes in each season
  -d DATES, --dates DATES
                        comma separated list of season dates (or True to use tvmaze airdates)
  -t TITLE, --title TITLE
                        title for the Kodi dialog box
  -m MSG, --msg MSG     message used in the Kodi dialog box (or 'tag-based' to
                        use tvmaze tag name based msg)
  -y TYPE, --type TYPE  the media type for the stub (must be a valid Kodi
                        type)
  -u TVMAZE_USER, --tvmaze_user TVMAZE_USER
                        the TV Maze user id (only needed for certain functions)
  -a TVMAZE_APIKEY, --tvmaze_apikey TVMAZE_APIKEY
                        the TV Maze api key (only needed for certain functions)
  -r, --streamfile      output as a stream file instead of a media stub
```

### Deciding Between Media Stubs and Stream Files
The script by default creates media stub files. If you are using Kodi and have a physical disc player attached, Kodi will display the message in the stub file. If you don't have a physical disc player attached, the media stubs won't work.  To get around that, I have written an addon called [plugin.whereareyou](https://kodi.wiki/view/Add-on:Where_Are_You) that will allow you to do something similar. If you are using plugin.whereareyou, you need to create the files as stream files using the `-r` option.

### Using the TV Maze options

#### from a List of TV Maze IDs
The good news is, this is free.  The bad news is that you have to maintain the list of ids manually. You can find TV Maze IDs for shows by searching for them at <https://tvmaze.com> and looking at the show's URL.
```
    python3 execute.py -i 42342,23030
```

#### from your Followed Recordings
If you have a TV Maze subscription (any level), you can use your followed shows as the list of shows from which to create stub/stream files.  You can either put your TV Maze credentials in settings.py or in the command line.
```
    python3 execute.py -i followed
```

#### from Tags
If you have a TV Maze subscription (any level), you can use your tags to only create stub/stream files for some shows.  You can include more than one tag by separating the tagids with commas. To find a tag id, go to your tag list and hover over one of them.  The URL will show the tag id. For instance, I label Netflix shows I add to a tag called NETFLIX.  You can either put your TV Maze credentials in settings.py or in the command line.
```
    python3 execute.py -i tags:9001
```

#### Adding Tag Specific Messages
If you're using TV Maze tags, you can have a custom message based on the tag name.
```
    python3 execute.py -i 42342,23030 -d True
```

#### Using Air Dates as File Creation Dates
To help with how Kodi sorts recently addded items, you can have the script use the TV Maze airdate for an episode as the file creation date.
```
    python3 execute.py -i tags:9001 -m tag-based
```



### Creating Seasons of TV Shows by Hand
You can use the script to create a season, or multiple seasons of TV shows.  Here are a few examples:

#### Creating a TV Show with a Single Season and Multiple Episodes

```
    python3 execute.py -n Daredevil -s 1 -e 13
```

#### Creating a TV Show with Multiple Seasons and Multiple Episodes

```
    python3 execute.py -n Daredevil -s 1,2,3 -e 13,13,13
```

### Creating a Movie

```
    python3 execute.py -n 'The Princess Bride'
```

### Adding Dates to Files
Kodi uses the file creation date to figure out how to sort things like recently added TV shows. The script can "back date" a series if you don't want it to flood your recently added shows list by using the `-d` flag. You would need to provide a comma separate list of the date for each season (sorry, no episode specific dating available) like this:

```
    -d 2015-04-10,2016-04-18,2018-10-19
```

The date format must match the one specified in the `dateformat` setting. If you only have one season (or what to date a movie), you can just provide the single date.  If you are using TV Maze, you can set this to `True` and the script will use the airdate from TV Maze as the file date.

### Changing the Title or Message in the Kodi Dialog Box
In addition to changing the default title and message in the settings file, you can also do it from the command line. This is useful, for instance, if you have some shows available from Netflix and others from Hulu. You would use the `-t` and `-m` flags to do this.

```
    -t 'Available on Hulu' -m 'This show is available from the Hulu app on the AppleTV.'
```

### Using the Settings File to Generate Files on a Schedule
Sometimes you may have a streaming show that is releasing episodes weekly instead of all at once.  You can add the `videos` option to the settings file and then run the script from cron so it can generate files for you after the episode becomes available.  The `videos` is a list of dicts. Each dict must have at least the date the file should be created and a name (if you're doing a movie). A TV show also needs an episode number (in Kodi's standard format of SxxExx). You can also include a custom title and message for the Kodi dialog box.  Here's an example of some of the variations:

```
    videos = [
               {'date':'2020-05-01', 'name':'Daredevil', 'episode':'S01E01', 'title':'On Netflix', 'msg':'Available via the TV Netflix app.' },
               {'date':'2020-05-07', 'name':'Daredevil', 'episode':'S01E02' },
               {'date':'2020-06-01', 'name':'Toy Story' }
             ]
```

To run the script from cron, you would need an entry in crontab file that looks something like this:

```
    00 02 * * * /usr/bin/python3 /path/to/create.kodi.mediastubs/execute.py -f
```






