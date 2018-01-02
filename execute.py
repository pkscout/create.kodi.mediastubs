# *  Credits:
# *
# *  v.1.0.0~beta4
# *  original Trigger Kodi Scan code by pkscout

import atexit, argparse, datetime, os, random, sys, time
import data.config as config
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


    def _init_vars( self ):
        self.DATAROOT = os.path.join( p_folderpath, 'data' )


    def _parse_argv( self ):
        parser = argparse.ArgumentParser()
        parser.add_argument( "-s", "--series", required=True, help="the name of the series" )
        parser.add_argument( "-e", "--seasons", required=True, help="comma separated list of the seasons to create" )
        parser.add_argument( "-p", "--episodes", required=True, help="comma separated list of the number of episodes in each season" )
        parser.add_argument( "-t", "--title", required=True, help="title for the Kodi dialog box" )
        parser.add_argument( "-m", "--msg", required=True, help="message used in the Kodi dialog box" )
        parser.add_argument( "-y", "--type", required=True, help="the media source for the stub (must be a valid Kodi type)" )
        self.ARGS = parser.parse_args()


    def _add_leading_zeros( self, num ):
        num = int( num )
        if num < 10:
            return '0' + str( num )
        else:
            return str( num )


    def _get_file_text( self ):
        replacement_dic = {'[TITLE]' : self.ARGS.title,
                           '[MESSAGE]' : self.ARGS.msg}
        loglines, template = readFile( os.path.join( self.DATAROOT, 'disc_template.txt' ) )
        lw.log (loglines )
        return replaceWords( template, replacement_dic )


    def _create_media_stubs( self ):
        series_name = self.ARGS.series
        season_list = self.ARGS.seasons.split( ',' )
        episode_list = self.ARGS.episodes.split( ',' )
        series_root = os.path.join( self.DATAROOT, series_name )
        stub_type = self.ARGS.type
        file_text = self._get_file_text()
        el_ref = 0
        success, log_lines = checkPath( series_root )
        lw.log( log_lines )
        for season in season_list:
            season_num = self._add_leading_zeros( season )
            try:
                max_eps = int( episode_list[el_ref] ) + 1
            except IndexError:
                break
            for e in range( 1, max_eps):
                ep_num = self._add_leading_zeros( e )
                file_name = '%s.S%sE%s.%s.disc' % (series_name, season_num, ep_num, stub_type )
                file_path = os.path.join( series_root, file_name )
                success, loglines = writeFile( file_text, file_path )
                lw.log( loglines )
            el_ref = el_ref + 1


if ( __name__ == "__main__" ):
    lw.log( ['script started'], 'info' )
    Main()
lw.log( ['script finished'], 'info' )