# create.kodi.medistubs
This script generates a set of text files you can use in Kodi for TV Series that are on Bluray discs (or some other outside source).  All series are created in a folder within the data directory of the script.  Once created you can move them to the appropriate place for Kodi to scrape.

usage: execute.py [-h] [-n NAME] [-s SEASONS] [-e EPISODES] [-d DATES]
                  [-t TITLE] [-m MSG] [-y TYPE] [-f] [-r]

optional arguments:
  -h, --help                       show this help message and exit
  -n NAME, --name NAME             the name of the series or movie
  -s SEASONS, --seasons SEASONS    comma separated list of the seasons to create
  -e EPISODES, --episodes EPISODES comma separated list of the number of episodes in each season
  -d DATES, --dates DATES          comma separated list of season dates
  -t TITLE, --title TITLE          title for the Kodi dialog box
  -m MSG, --msg MSG                message used in the Kodi dialog box
  -y TYPE, --type TYPE             the media type for the stub (must be a valid Kodi type)
  -f, --fromsettings               generate file based on airdate of episodes in settingsfile
  -r, --streamfile                 output as a stream file instead of a media stub
  
