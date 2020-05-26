defaults = { 'illegalchars': '<>:"/\|?*',
             'illegalreplace': '_',
             'endreplace': '',
             'dateformat': '%Y-%m-%d',
             'tvmaze_user': '',
             'tvmaze_apikey': '',
             'tvmaze_wait': 0.12,
             'title': 'Available Streaming',
             'msg': 'This video is available from a streaming service on another device',
             'rootpath': None,
             'tvroot': 'TVShows',
             'movieroot': 'Movies',
             'videos': [],
             'aborttime': 30,
             'logbackups': 7,
             'debug': False }

try:
    import data.settings as overrides
    has_overrides = True
except ImportError:
    has_overrides = False


def Reload():
    if has_overrides:
        reload( overrides )


def Get( name ):
    setting = None
    if has_overrides:
        setting = getattr(overrides, name, None)
    if not setting:
        setting = defaults.get( name, None )
    return setting
    