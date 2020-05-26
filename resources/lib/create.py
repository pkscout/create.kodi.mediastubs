# v.0.4.1

import atexit, argparse, os, random, sys, time
from datetime import date, timedelta
import resources.config as config
from urllib.parse import urlencode, quote_plus
from resources.lib.fileops import checkPath, deleteFile, osPathFromString, setSafeName, writeFile
from resources.lib.tvmazeapi import TVMaze
from resources.lib.xlogger import Logger
from configparser import *

p_folderpath, p_filename = os.path.split( sys.argv[0] )
logpath = os.path.join( p_folderpath, 'data', 'logs', '' )
checkPath( logpath )
lw = Logger( logfile=os.path.join( logpath, 'logfile.log' ), numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )

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
        group.add_argument( "-n", "--name", help="the name of the series/movie" )
        group.add_argument( "-f", "--source", help="generate file based on either 'settings' or 'tvmaze'")
        parser.add_argument( "-i", "--tvmazeids", help="TV Maze IDs (comma sep), 'followed', or 'tags:tagids' (comma sep)" )
        parser.add_argument( "-l", "--lookback", help="number of days backwards in time to look for episode match" )
        parser.add_argument( "-s", "--seasons", help="comma separated list of the seasons to create" )
        parser.add_argument( "-e", "--episodes", help="comma separated list of the number of episodes in each season" )
        parser.add_argument( "-d", "--dates", help="comma separated list of season dates (or True to use tvmaze airdates)" )
        parser.add_argument( "-t", "--title", help="title for the Kodi dialog box" )
        parser.add_argument( "-m", "--msg", help="message used in the Kodi dialog box (or 'tag-based' to use tvmaze tag name based msg)" )
        parser.add_argument( "-y", "--type", help="the media type for the stub (must be a valid Kodi type)" )
        parser.add_argument( "-u", "--tvmaze_user", help="the TV Maze user id (only needed for certain functions)" )
        parser.add_argument( "-a", "--tvmaze_apikey", help="the TV Maze api key (only needed for certain functions)" )
        parser.add_argument( "-r", "--streamfile", action="store_true", help="output as a stream file instead of a media stub")
        self.ARGS = parser.parse_args()


    def _init_vars( self ):
        self.DATAROOT = config.Get( 'rootpath' )
        self.TVMAZEWAIT = config.Get( 'tvmaze_wait' )
        if self.DATAROOT:
            self.DATAROOT = osPathFromString( self.DATAROOT )
        else:
            self.DATAROOT = os.path.join( p_folderpath, 'data' )
        self.ILLEGALCHARS = list( config.Get( 'illegalchars' ) )
        self.ILLEGALREPLACE = config.Get( 'illegalreplace' )
        self.ENDREPLACE = config.Get( 'endreplace' )
        if self.ARGS.dates:
            self.DATELIST = self.ARGS.dates.split( ',' )
        else:
            self.DATELIST = None
        if self.ARGS.title:
            self.TITLE = self.ARGS.title
        else:
            self.TITLE = config.Get( 'title' )
        if self.ARGS.msg:
            self.MSG = self.ARGS.msg
        else:
            self.MSG = config.Get( 'msg' )
        if self.ARGS.tvmaze_user:
            tvmaze_user = self.ARGS.tvmaze_user
        else:
            tvmaze_user = config.Get( 'tvmaze_user' )
        if self.ARGS.tvmaze_apikey:
            tvmaze_apikey = self.ARGS.tvmaze_apikey
        else:
            tvmaze_apikey = config.Get( 'tvmaze_apikey' )
        self.TVMAZE = TVMaze( user=tvmaze_user, apikey=tvmaze_apikey )
        self.TAGNAMEMAP = {}
        if self.MSG == 'tag-based':
            success, loglines, results = self.TVMAZE.getTags()
            lw.log( loglines )
            if success:
                for result in results:
                    try:
                        self.TAGNAMEMAP[str( result['id'] )] = result['name']
                    except KeyError:
                        lw.log( 'no id or name found, aborting' )
                        break


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
        if self.ARGS.source == 'settings':
            self._create_stubs_from_settings( media_type, ext )
        elif self.ARGS.source == 'tvmaze':
            self._create_stubs_from_tvmazeids( media_type, ext )
        elif self.ARGS.source:
            lw.log( ['invalid argument for source: %s' % self.ARGS.source] )
        else:
            self._create_stubs_from_args( media_type, ext )


    def _create_stubs_from_args( self, media_type='', ext='disc' ):
        file_text = self._get_file_text()
        video_name, loglines = setSafeName( self.ARGS.name, illegalchars=self.ILLEGALCHARS,
                                            illegalreplace=self.ILLEGALREPLACE, endreplace=self.ENDREPLACE )
        lw.log( loglines )
        video_path = os.path.join( self.DATAROOT, config.Get( 'tvroot' ), video_name )
        try:
            season_list = self.ARGS.seasons.split( ',' )
            episode_list = self.ARGS.episodes.split( ',' )
        except AttributeError as e:
            video_path = os.path.join( self.DATAROOT, config.Get( 'movieroot' ), video_name )
            season_list = []
            episode_list = []
        success, loglines = checkPath( video_path )
        lw.log( loglines )
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
                self._write_stub( file_path, file_text, setdate=self.DATELIST[ref] )
            ref = ref + 1
        if not season_list:
            file_name = '%s%s.%s' % (video_name, media_type, ext )
            file_path = os.path.join( video_path, file_name )
            self._write_stub( file_path, file_text )


    def _create_stubs_from_settings( self, media_type='', ext='disc' ):
        for video in config.Get( 'videos' ):
            lw.log( ['checking settings date %s against today %s' % (video.get( 'date' ), date.today().strftime( config.Get( 'dateformat' ) ))] )
            if video.get( 'date' ) == date.today().strftime( config.Get( 'dateformat' ) ):
                file_text = self._get_file_text( video.get( 'title' ), video.get( 'msg' ))
                video_name, loglines = setSafeName( video.get( 'name' ), illegalchars=self.ILLEGALCHARS,
                                                    illegalreplace=self.ILLEGALREPLACE, endreplace=self.ENDREPLACE )
                lw.log( loglines )
                if video.get( 'episode' ):
                    video_path = os.path.join( self.DATAROOT, config.Get( 'tvroot' ), video_name )
                    file_name = '%s.%s.%s' % (video_name, video.get( 'episode' ), ext)
                else:
                    video_path = os.path.join( self.DATAROOT, config.Get( 'movieroot' ), video_name )
                    file_name = '%s.%s' % (video_name, ext)
                success, loglines = checkPath( video_path )
                lw.log( loglines )
                file_path = os.path.join( video_path, file_name )
                self._write_stub( file_path, file_text, setdate=self.DATELIST[ref] )


    def _create_stubs_from_tvmazeids( self, media_type='', ext='disc' ):
        if self.ARGS.tvmazeids == 'followed':
            success, loglines, results = self.TVMAZE.getFollowedShows()
            lw.log( loglines )
            items = self._extract_tvmaze_showids( results )
            lw.log( ['continuing with updated list of shows of:', items] )
        elif 'tags' in self.ARGS.tvmazeids:
            items = []
            tag_show_map = {}
            try:
                tags = self.ARGS.tvmazeids.split( ':' )[1].split( ',' )
            except IndexError:
                tags = []
                lw.log( ['no tags found in tags call'] )
            for tag in tags:
                success, loglines, results = self.TVMAZE.getTaggedShows( tag )
                lw.log( loglines )
                show_ids = self._extract_tvmaze_showids( results )
                items.extend( show_ids )
                for show_id in show_ids:
                    tag_show_map[show_id] = tag
            lw.log( ['continuing with updated list of show ids of:', items] )
        else:
            items = self.ARGS.tvmazeids.split( ',' )
        for item in items:
            success, loglines, show = self.TVMAZE.getShow( item, params={'embed':'episodes'} )
            lw.log( loglines )
            if not success:
                lw.log( ['got nothing back from TVMaze, skipping'] )
                continue
            time.sleep( self.TVMAZEWAIT )
            try:
                showname = show['name']
                episodes = show["_embedded"]['episodes']
            except KeyError:
                lw.log( ['no valid show name and/or episode list, skipping'] )
                continue
            old_msg = self.MSG
            if self.TAGNAMEMAP and tag_show_map:
                self.MSG = 'Available on %s' % self.TAGNAMEMAP[tag_show_map[item]]
                lw.log( ['message set to: %s' % self.MSG] )
            file_text = self._get_file_text()
            self.MSG = old_msg
            video_name, loglines = setSafeName( showname, illegalchars=self.ILLEGALCHARS,
                                                illegalreplace=self.ILLEGALREPLACE, endreplace=self.ENDREPLACE )
            lw.log( loglines )
            video_path = os.path.join( self.DATAROOT, config.Get( 'tvroot' ), video_name )
            success, loglines = checkPath( video_path )
            lw.log( loglines )
            if self.ARGS.lookback:
                checkdateraw = date.today() - timedelta( days=int( self.ARGS.lookback ) )
                checkdate = checkdateraw.strftime( config.Get( 'dateformat' ) )
                lw.log( ['checking for epsiode matches based on date of %s' % checkdate] )
            for episode in episodes:
                if self.ARGS.lookback:
                    if not episode.get( 'airdate' ) in checkdate:
                        continue
                if self.ARGS.seasons:
                    if not str( episode.get( 'season' ) ) in self.ARGS.seasons:
                        continue
                if self.ARGS.episodes:
                    if not str( episode.get( 'number' ) ) in self.ARGS.episodes:
                        continue
                ep_name, loglines = setSafeName( episode.get( 'name' ), illegalchars=self.ILLEGALCHARS,
                                                 illegalreplace=self.ILLEGALREPLACE, endreplace=self.ENDREPLACE )
                lw.log( loglines )
                ep_season = self._add_leading_zeros( episode.get( 'season' ) )
                ep_number = self._add_leading_zeros( episode.get( 'number' ) )
                if not ep_season and not ep_number:
                    lw.log( ['need both season and episode number to create a valid file, skipping'] )
                    continue
                if ep_name:
                    full_episode = 'S%sE%s.%s' % (ep_season, ep_number, ep_name)
                else:
                    full_episode = 'S%sE%s' % (ep_season, ep_number)                
                file_name = '%s.%s.%s' % (video_name, full_episode, ext)
                file_path = os.path.join( video_path, file_name )
                if self.ARGS.dates:
                    self._write_stub( file_path, file_text, setdate=episode.get( 'airdate' ) )
                else:
                    self._write_stub( file_path, file_text )


    def _extract_tvmaze_showids( self, results ):
        items = []
        if self._check_results( results ):
            for show in results:
                try:
                    items.append( show['show_id'] )
                except KeyError:
                    continue
        return items


    def _check_results( self, results ):
        try:
            check_results = results[0]['show_id']
        except (IndexError, KeyError):
            return False
        return True


    def _get_file_text( self, title='', msg='' ):
        if not title:
            title = self.TITLE
        if not msg:
            msg = self.MSG
        if self.ARGS.streamfile:
            return 'plugin://plugin.whereareyou?empty=pad&%s' % urlencode( {'title':title, 'message':msg}, quote_via=quote_plus )
        else:
            return '<discstub>\r    <title>%s</title>\r    <message>%s</message>\r</discstub>' % (title, msg)

    def _write_stub( self, file_path, file_text, setdate='' ):
        success, loglines = writeFile( file_text, file_path, 'w' )
        lw.log( loglines )
        if success and setdate:
            t = time.mktime( time.strptime( setdate, config.Get( 'dateformat' ) ) )
            os.utime( file_path, (t,t) )

