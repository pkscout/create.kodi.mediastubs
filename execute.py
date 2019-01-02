# *  Credits:
# *
# *  v.0.1.0
# *  original Create Kodi Media Stubs code by pkscout

import atexit, argparse, datetime, os, random, sys, time
import resources.config as config
from urllib.parse import urlencode, quote_plus
from resources.common.xlogger import Logger
from resources.common.fileops import deleteFile, readFile, writeFile, checkPath
from resources.common.transforms import replaceWords
if sys.version_info < (3, 0):
    from ConfigParser import *
else:
    from configparser import *

p_folderpath, p_filename = os.path.split( os.path.realpath(__file__) )
lw = Logger( logfile = os.path.join( p_folderpath, 'data', 'logfile.log' ),
             numbackups = config.Get( 'logbackups' ), logdebug = str( config.Get( 'debug' ) ) )

def _deletePID():
    success, loglines = deleteFile( pidfile )
    lw.log (loglines )

pid = str(os.getpid())
pidfile = os.path.join( p_folderpath, 'data', 'create.pid' )
atexit.register( _deletePID )


class Main:
    def __init__( self ):
        self._setPID()
        self._parse_argv()
        self._init_vars()
        self._create_media_stubs()
        
                
    def _setPID( self ):
        basetime = time.time()
        while os.path.isfile( pidfile ):
            time.sleep( random.randint( 1, 3 ) )
            if time.time() - basetime > config.Get( 'aborttime' ):
                err_str = 'taking too long for previous process to close - aborting attempt'
                lw.log( [err_str] )
                sys.exit( err_str )
        lw.log( ['setting PID file'] )
        success, loglines = writeFile( pid, pidfile )
        lw.log( loglines )        


    def _parse_argv( self ):
        parser = argparse.ArgumentParser()
        parser.add_argument( "-s", "--series", required=True, help="the name of the series (required)" )
        parser.add_argument( "-e", "--seasons", required=True, help="comma separated list of the seasons to create (required)" )
        parser.add_argument( "-p", "--episodes", required=True, help="comma separated list of the number of episodes in each season (required)" )
        parser.add_argument( "-d", "--dates", help="comma separated list of season dates" )        
        parser.add_argument( "-t", "--title", help="title for the Kodi dialog box" )
        parser.add_argument( "-m", "--msg", help="message used in the Kodi dialog box" )
        parser.add_argument( "-y", "--type", help="the media source for the stub (must be a valid Kodi type)" )
        parser.add_argument( "-r", "--streamfile", action="store_true", help="output as a stream file instead of a media stub")
        self.ARGS = parser.parse_args()


    def _init_vars( self ):
        self.DATAROOT = os.path.join( p_folderpath, 'data' )
        self.ILLEGALCHARS = list( config.Get( 'illegalchars' ) )
        self.ILLEGALREPLACE = config.Get( 'illegalreplace' )
        self.ENDREPLACE = config.Get( 'endreplace' )
            

    def _add_leading_zeros( self, num ):
        num = int( num )
        if num < 10:
            return '0' + str( num )
        else:
            return str( num )


    def _create_media_stubs( self ):
        series_name = self._set_safe_name( self.ARGS.series )
        season_list = self.ARGS.seasons.split( ',' )
        episode_list = self.ARGS.episodes.split( ',' )
        if self.ARGS.dates:
            date_list = self.ARGS.dates.split( ',' )
        else:
            date_list = None
        series_root = os.path.join( self.DATAROOT, series_name )
        if self.ARGS.type:
            stub_type = '.' + self.ARGS.type
        else:
           stub_type = ''
        file_text = self._get_file_text()
        ref = 0
        success, log_lines = checkPath( series_root )
        lw.log( log_lines )
        for season in season_list:
            season_num = self._add_leading_zeros( season )
            try:
                max_eps = int( episode_list[ref] ) + 1
            except IndexError:
                break
            for e in range( 1, max_eps):
                ep_num = self._add_leading_zeros( e )
                if self.ARGS.streamfile:
                    ext = 'strm'
                else:
                    ext = 'disc'
                file_name = '%s.S%sE%s%s.%s' % (series_name, season_num, ep_num, stub_type, ext )
                file_path = os.path.join( series_root, file_name )
                success, loglines = writeFile( file_text, file_path, 'w' )
                lw.log( loglines )
                if success and date_list:
                    t = time.mktime(time.strptime(date_list[ref], config.Get( 'dateformat' )))
                    os.utime(file_path, (t,t))
            ref = ref + 1


    def _get_file_text( self ):
        if self.ARGS.title:
            title = self.ARGS.title
        else:
            title = ''
        if self.ARGS.msg:
            message = self.ARGS.msg
        else:
            message = ''
        if title or message:
            if self.ARGS.streamfile:
                return 'plugin://plugin.whereareyou?empty=pad&%s' % urlencode( {'title':title, 'message':message}, quote_via=quote_plus )
            else:
                replacement_dic = {'[TITLE]' : title,
                                   '[MESSAGE]' : message}
                loglines, template = readFile( os.path.join( self.DATAROOT, 'disc_template.txt' ) )
                lw.log (loglines )
                return replaceWords( template, replacement_dic )
        else:
            return ''


    def _remove_trailing_dot( self, thename ):
        if thename[-1] == '.' and len( thename ) > 1 and self.ENDREPLACE is not '.':
            return self._remove_trailing_dot( thename[:-1] + self.ENDREPLACE )
        else:
            return thename


    def _set_safe_name( self, name ):
        s_name = ''
        lw.log( ['the illegal characters are ', self.ILLEGALCHARS, 'the replacement is ' + self.ILLEGALREPLACE] )
        for c in list( self._remove_trailing_dot( name ) ):
            if c in self.ILLEGALCHARS:
                s_name = s_name + self.ILLEGALREPLACE
            else:
                s_name = s_name + c  
        return s_name


if ( __name__ == "__main__" ):
    lw.log( ['script started'], 'info' )
    Main()
lw.log( ['script finished'], 'info' )