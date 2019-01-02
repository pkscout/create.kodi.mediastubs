# create.kodi.medistubs
This script generates a set of text files you can use in Kodi for TV Series that are on Bluray discs (or some other outside source).  All series are created in a folder within the data directory of the script.  Once created you can move them to the appropriate place for Kodi to scrape.

usage: execute.py [-h] -s SERIES -e SEASONS -p EPISODES [-d DATES] [-t TITLE]
                  [-m MSG] [-y TYPE] [-r]

optional arguments:
  -h, --help            show this help message and exit
  -s SERIES, --series SERIES
                        the name of the series (required)
  -e SEASONS, --seasons SEASONS
                        comma separated list of the seasons to create
                        (required)
  -p EPISODES, --episodes EPISODES
                        comma separated list of the number of episodes in each
                        season (required)
  -d DATES, --dates DATES
                        comma separated list of season dates
  -t TITLE, --title TITLE
                        title for the Kodi dialog box
  -m MSG, --msg MSG     message used in the Kodi dialog box
  -y TYPE, --type TYPE  the media source for the stub (must be a valid Kodi
                        type)
  -r, --streamfile      output as a stream file instead of a media stub
  
