# *  Credits:
# *
# *  v.0.4.0
# *  original Create Kodi Media Stubs code by pkscout

import atexit, argparse, os, random, sys, time
from datetime import date
import resources.config as config
from urllib.parse import urlencode, quote_plus
from resources.lib.xlogger import Logger
from resources.lib.fileops import checkPath, deleteFile, osPathFromString, writeFile
from configparser import *

p_folderpath, p_filename = os.path.split( sys.argv[0] )
logpath = os.path.join( p_folderpath, 'data', 'logs', '' )
checkPath( logpath )
lw = Logger( logfile = os.path.join( logpath, 'logfile.log' ), numbackups = config.Get( 'logbackups' ), logdebug = str( config.Get( 'debug' ) ) )

def _deletePID():
    success, loglines = deleteFile( pidfile )
    lw.log (loglines )
    lw.log( ['script stopped'], 'info' )

pid = str(os.getpid())
pidfile = os.path.join( p_folderpath, 'data', 'create.pid' )
atexit.register( _deletePID )



class Main:
    def __init__( self ):
        lw.log( ['script started'], 'info' )
        self._setPID()
        self._parse_argv()
        self._init_vars()
        self._create_stubs()


    def _setPID( self ):
        basetime = time.time()
        while os.path.isfile( pidfile ):
            time.sleep( random.randint( 1, 3 ) )
            if time.time() - basetime > config.Get( 'aborttime' ):
                err_str = 'taking too long for previous process to close - aborting attempt'
                lw.log( [err_str] )
                sys.exit( err_str )
        lw.log( ['setting PID file'] )
        success, loglines = writeFile( pid, pidfile, 'w' )
        lw.log( loglines )


    def _parse_argv( self ):
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument( "-n", "--name", help="the name of the series or movie" )
        group.add_argument( "-f", "--fromsettings", action="store_true", help="generate file based on airdate of episodes in settings file")
        parser.add_argument( "-s", "--seasons", help="comma separated list of the seasons to create" )
        parser.add_argument( "-e", "--episodes", help="comma separated list of the number of episodes in each season" )
        parser.add_argument( "-d", "--dates", help="comma separated list of season dates" )
        parser.add_argument( "-t", "--title", help="title for the Kodi dialog box" )
        parser.add_argument( "-m", "--msg", help="message used in the Kodi dialog box" )
        parser.add_argument( "-y", "--type", help="the media type for the stub (must be a valid Kodi type)" )
        parser.add_argument( "-r", "--streamfile", action="store_true", help="output as a stream file instead of a media stub")
        self.ARGS = parser.parse_args()


    def _init_vars( self ):
        self.DATAROOT = config.Get( 'rootpath' )
        if self.DATAROOT:
            self.DATAROOT = osPathFromString( self.DATAROOT )
        else:
            self.DATAROOT = os.path.join( p_folderpath, 'data' )
        self.ILLEGALCHARS = list( config.Get( 'illegalchars' ) )
        self.ILLEGALREPLACE = config.Get( 'illegalreplace' )
        self.ENDREPLACE = config.Get( 'endreplace' )
        if self.ARGS.title:
            self.TITLE = self.ARGS.title
        else:
            self.TITLE = config.Get( 'title' )
        if self.ARGS.msg:
            self.MSG = self.ARGS.msg
        else:
            self.MSG = config.Get( 'msg' )


    def _add_leading_zeros( self, num ):
        num = int( num )
        if num < 10:
            return '0' + str( num )
        else:
            return str( num )


    def _create_stubs( self ):
        if self.ARGS.type:
            media_type = '.' + self.ARGS.type
        else:
           media_type = ''
        if self.ARGS.streamfile:
            ext = 'strm'
        else:
            ext = 'disc'
        if self.ARGS.fromsettings:
            for video in config.Get( 'videos' ):
                lw.log( ['checking settings date %s against today %s' % (video.get( 'date' ), date.today().strftime( config.Get( 'dateformat' ) ))] )
                if video.get( 'date' ) == date.today().strftime( config.Get( 'dateformat' ) ):
                    file_text = self._get_file_text( video.get( 'title' ), video.get( 'msg' ))
                    video_name = self._set_safe_name( video.get( 'name' ) )
                    if video.get( 'episode' ):
                        video_path = os.path.join( self.DATAROOT, config.Get( 'tvroot' ), video_name )
                        file_name = '%s.%s.%s' % (video_name, video.get( 'episode' ), ext)
                    else:
                        video_path = os.path.join( self.DATAROOT, config.Get( 'movieroot' ), video_name )
                        file_name = '%s.%s' % (video_name, ext)
                    success, loglines = checkPath( video_path )
                    lw.log( loglines )
                    success, loglines = writeFile( file_text, os.path.join( video_path, file_name ), 'w' )
                    lw.log( loglines )
        else:
            file_text = self._get_file_text()
            video_name = self._set_safe_name( self.ARGS.name )
            video_path = os.path.join( self.DATAROOT, config.Get( 'tvroot' ), video_name )
            success, loglines = checkPath( video_path )
            lw.log( loglines )
            try:
                season_list = self.ARGS.seasons.split( ',' )
                episode_list = self.ARGS.episodes.split( ',' )
            except AttributeError as e:
                video_path = os.path.join( self.DATAROOT, config.Get( 'movieroot' ), video_name )
                season_list = []
                episode_list = []
            if self.ARGS.dates:
                date_list = self.ARGS.dates.split( ',' )
            else:
                date_list = None
            ref = 0
            for season in season_list:
                season_num = self._add_leading_zeros( season )
                try:
                    max_eps = int( episode_list[ref] ) + 1
                except IndexError:
                    break
                for e in range( 1, max_eps):
                    ep_num = self._add_leading_zeros( e )
                    file_name = '%s.S%sE%s%s.%s' % (video_name, season_num, ep_num, media_type, ext )
                    file_path = os.path.join( video_path, file_name )
                    success, loglines = writeFile( file_text, file_path, 'w' )
                    lw.log( loglines )
                    if success and date_list:
                        t = time.mktime(time.strptime(date_list[ref], config.Get( 'dateformat' )))
                        os.utime(file_path, (t,t))
                ref = ref + 1
            if not season_list:
                file_name = '%s%s.%s' % (video_name, media_type, ext )
                file_path = os.path.join( video_path, file_name )
                success, loglines = writeFile( file_text, file_path, 'w' )
                lw.log( loglines )


    def _get_file_text( self, title='', msg='' ):
        if not title:
            title = self.TITLE
        if not msg:
            msg = self.MSG
        if self.ARGS.streamfile:
            return 'plugin://plugin.whereareyou?empty=pad&%s' % urlencode( {'title':title, 'message':msg}, quote_via=quote_plus )
        else:
            return '<discstub>\r    <title>%s</title>\r    <message>%s</message>\r</discstub>' % (title, msg)


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
