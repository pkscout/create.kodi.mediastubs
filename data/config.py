defaults = { 'illegalchars': '<>:"/\|?* ',
             'illegalreplace': '.',
             'endreplace': '',
             'dateformat': '%Y-%m-%d',
             'aborttime': 30,
             'logbackups': 1,
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
    