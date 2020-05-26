#v.0.3.0

from resources.lib.url import URL
JSONURL = URL( 'json' )
TXTURL = URL()


class TVMaze( object ):

    def __init__( self, user='', apikey='' ):
        self.PUBLICURL = 'https://api.tvmaze.com'
        if user and apikey:
            self.AUTHURL = 'https://%s:%s@api.tvmaze.com/v1/user' % (user, apikey)
        else:
            self.AUTHURL = self.PUBLICURL


    def getShow( self, tvmazeid, params=None ):
        return self._call( 'shows/%s' % tvmazeid, params )


    def getEpisode( self, episodeid, params=None ):
        return self._call( 'episodes/%s' % episodeid, params )


    def getFollowedShows( self, params=None ):
        return self._call( 'follows/shows', params, auth=True )


    def getTaggedShows( self, tag, params=None ):
        return self._call( 'tags/%s/shows' % tag, params, auth=True )


    def unTagShow( self, show, tag, params=None ):
        return self._call( 'tags/%s/shows/%s' % (tag, show), params, auth=True, type='delete' )


    def getTags( self, params=None ):
        return self._call( 'tags', params, auth=True )


    def _call( self, url_end, params, auth=False, type="get" ):
        loglines = []
        if not params:
            params = {}
        if auth:
            if self.AUTHURL == self.PUBLICURL:
                loglines.append( 'authorization credentials required but not supplied' )
                return False, loglines, {}
            url_base = self.AUTHURL
        else:
            url_base = self.PUBLICURL
        url = '%s/%s' % (url_base, url_end )
        if type == 'get':
            success, j_loglines, results = JSONURL.Get( url, params=params )
        if type == 'delete':
            success, j_loglines, results = TXTURL.Delete( url, params=params )
        loglines = loglines + j_loglines
        return success, loglines, results
