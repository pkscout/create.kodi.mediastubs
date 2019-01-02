# v.0.1.0
    
import os, re
from .fileops import readFile, writeFile
from datetime import datetime, date, timedelta
try:
    smb_installed = True
    import smb
    from smb.SMBConnection import SMBConnection
except ImportError:
    smb_installed = False
try:
    chilkat_installed = True
    import chilkat
except ImportError:
    chilkat_installed = False

def parseSettings( config, settings ):
        pconfig = {}
        pconfig['localdownloadpath'] = os.path.join( settings.get( 'dataroot' ), 'downloads' )
        pconfig['hostkey'] = os.path.join( settings.get( 'dataroot' ), 'keys', settings.get( 'name' ) + '_host.key' )
        pconfig['privatekey'] = os.path.join( settings.get( 'dataroot' ), 'keys', settings.get( 'name' ) + '_private.key' )
        pconfig['sourcefolder'] = _parse_items( settings.get( 'sourcefolders' ) ).get( settings.get( 'sourcefolder_default' ),
                                                settings.get( 'sourcefolder_default' ) )
        override_dateformat = config.Get( 'override_dateformat' )
        regular_dateformat = settings.get( 'dateformat', config.Get( 'dateformat' ) )
        if settings.get( 'override_date' ):
            dateformat = override_dateformat
        else:
            dateformat = regular_dateformat
        thedate = settings.get( 'override_date', settings.get( 'filter' ) )
        try:
            pconfig['remotefilter'] = datetime.strptime( thedate, dateformat ).date().strftime( regular_dateformat )
        except TypeError as e:
            pconfig['remotefilter'] = (date.today() - timedelta( 1 )).strftime( dateformat )
        except ValueError as e:        
            pconfig['remotefilter'] = thedate
        return pconfig


def checkHostkey( key, file ):
    loglines = []
    rloglines, saved_key = readFile( file )
    loglines.extend( rloglines )
    if not saved_key:
        success, wloglines = writeFile( key, file, 'w' )
        loglines.extend( wloglines )
        saved_key = key
    return saved_key == key, loglines
    

def _parse_items( items, itemdelim = ',', subitemdelim = ':' ):
    if subitemdelim:
        items_group = {}
    else:
        items_group = []
    if not items:
        return items_group
    itemlist = items.split( itemdelim )
    for item in itemlist:
        if subitemdelim:
            item_parts = item.split( subitemdelim )
            items_group[item_parts[0].strip()] = item_parts[1].strip()
        else:
            items_group.append( item.strip() )
    return items_group

   
class SFTP:
    def __init__( self, settings ):
        self.SETTINGS = settings
    
    
    def _connect( self ):
        if not chilkat_installed:
            return False, ['chilkat python module is not installed. Please see README.md for prequisite and install instructions.']
        loglines = []
        key = chilkat.CkSshKey()
        privatekey = key.loadText( self.SETTINGS.get( 'privatekey' ) )
        if key.get_LastMethodSuccess() == True:
            if self.SETTINGS.get( 'key_auth' ):
                key.put_Password( self.SETTINGS.get( 'key_auth' ) );
            success = key.FromOpenSshPrivateKey( privatekey )
            if not success:
                key = None   
        else:
            key = None
        loglines.append( 'connecting to %s server' % self.SETTINGS.get( 'module_name', '' ) )
        sftp = chilkat.CkSFtp()
        success = sftp.UnlockComponent( self.SETTINGS.get( 'chilkat_license', 'Anything for 30 day trial' ) )
        if not success:
            loglines.append( sftp.lastErrorText() )
            return False, loglines
        sftp.put_ConnectTimeoutMs( self.SETTINGS.get( 'timeout', 15000 ) )
        sftp.put_IdleTimeoutMs( self.SETTINGS.get( 'timeout', 15000 ) )
        success = sftp.Connect( self.SETTINGS.get( 'host' ), self.SETTINGS.get( 'port', 22 ) )
        if not success:
            loglines.append( sftp.lastErrorText() )
            return False, loglines
        success, cloglines = checkHostkey( sftp.hostKeyFingerprint(), self.SETTINGS.get( 'hostkey' ) )
        if self.SETTINGS.get( 'debug' ):
            loglines.extend( cloglines )
        if not success:
            loglines.append( 'WARNING: HOSTKEY FOR %s SERVER DOES NOT MATCH SAVED KEY. ABORTING.' % self.SETTINGS.get( 'module_name', '' ).upper() )
            return False, loglines
        if key:
            loglines.append( 'trying to authenticate using private key' )
            success = sftp.AuthenticatePk( self.SETTINGS.get( 'username', '' ), key )
        else:
            success = False
        if not success:
            if key and self.SETTINGS.get( 'debug' ):
                loglines.append( sftp.lastErrorText() )
            elif key:
                loglines.append( 'private key based authentication failed' )
            loglines.append( 'trying to authenticate with username and password' )
            success = sftp.AuthenticatePw( self.SETTINGS.get( 'username', '' ), self.SETTINGS.get( 'auth', '' ) )
            if not success:
                loglines.append( sftp.lastErrorText() )
                return False, loglines
        success = sftp.InitializeSftp()
        if not success:
            loglines.append( sftp.lastErrorText() )
            return False, loglines
        return sftp, loglines
 
 
    def Download( self, destination, filter='', path='' ):
        loglines = []
        dlist = []
        sftp, cloglines = self._connect()
        loglines.extend( cloglines )
        if not sftp:
            return False, loglines
        handle = sftp.openDir( path )
        if (sftp.get_LastMethodSuccess() != True):
            loglines.append( sftp.lastErrorText() )
            return False, loglines
        dirlisting = sftp.ReadDir( handle )
        if (sftp.get_LastMethodSuccess() != True):
            loglines.append( sftp.lastErrorText() )
            return False, loglines
        n = dirlisting.get_NumFilesAndDirs()
        if n == 0:
            loglines.append( 'no files in directory' )
        else:
            for i in range( 0, n ):
                filename = dirlisting.GetFileObject( i ).filename()
                if path:
                    remotefile = '/'.join( [path, filename] )
                else:
                    remotefile = filename
                if self.SETTINGS.get( 'debug' ):
                    loglines.append( 'checking file ' + filename )
                if re.search( filter, filename ):
                    localfile = os.path.join( destination, filename )
                    success = sftp.DownloadFileByName( remotefile, localfile )
                    if success == True:
                        loglines.append( 'downloaded %s to %s' % (remotefile, localfile) )
                        dlist.append( filename )
                        if self.SETTINGS.get( 'deleteafterdownload' ):
                            success = sftp.RemoveFile( remotefile )
                            if success:
                                loglines.append( 'deleted file %s from sftp site' % filename )
                            else:
                                loglines.extend( ['unable to delete file', sftp.lastErrorText()] ) 
                    else:
                        loglines.append( 'unable to download %s to %s' % (remotefile, localfile) )
                        if self.SETTINGS.get( 'debug' ):
                           loglines.append( sftp.lastErrorText() ) 
        success = sftp.CloseHandle( handle )
        if not success and self.SETTINGS.get( 'debug' ):
            loglines.append( sftp.lastErrorText() )
        if not dlist:
            loglines.append( 'no files matching filter ' + filter )
        return dlist, loglines


    def Upload( self, files, origin, path='' ):
        loglines = []
        sftp, cloglines = self._connect()
        loglines.extend( cloglines )
        if not sftp:
            return False, loglines
        fsuccess = True
        for file in files:        
            loglines.append( 'transferring file ' + file )
            remotefilepath = '/'.join( [path, file] )
            localfilepath = os.path.join( origin, file )
            success = sftp.UploadFileByName(remotefilepath,localfilepath)
            if not success:
                loglines.append( ftps.lastErrorText() )
                fsuccess = False
        loglines.append( 'disconnecting from SFTP server' )
        success = sftp.Disconnect()
        if not success and self.SETTINGS.get( 'debug' ):
            loglines.append( sftp.lastErrorText() )
        return fsuccess, loglines



class FTPS:    
    def __init__( self, settings ):
        self.SETTINGS = settings

    
    def _connect( self ):
        if not chilkat_installed:
            return False, ['chilkat python module is not installed. Please see README.md for prequisite and install instructions.']
        loglines = []
        ftps = chilkat.CkFtp2()
        success = ftps.UnlockComponent( self.SETTINGS.get( 'chilkat_license', 'Anything for 30 day trial' ) )
        if not success:
            loglines.append( ftps.lastErrorText() )
            return False, loglines
        loglines.append( 'connecting to %s server' % self.SETTINGS.get( 'module_name', '' ) )
        ftps.put_Passive( self.SETTINGS.get( 'passive', False ) )
        ftps.put_Hostname( self.SETTINGS.get( 'host' ) )
        ftps.put_Username( self.SETTINGS.get( 'username' ) )
        ftps.put_Password( self.SETTINGS.get( 'auth' ) )
        ftps.put_Port( self.SETTINGS.get( 'port', 990 ) )
        ftps.put_AuthTls( self.SETTINGS.get( 'authtls', True ) )
        ftps.put_Ssl( self.SETTINGS.get( 'ssl', False ) )
        success = ftps.Connect()
        if not success:
            loglines.append( ftps.lastErrorText() )
            return False, loglines
        return ftps, loglines
    

    def Download( self, destination, filter='', path='' ):
        loglines = []
        dlist = []
        ftps, cloglines = self._connect()
        loglines.extend( cloglines )
        if not ftps:
            return False, loglines
        if path:
            success = ftps.ChangeRemoteDir( path )
            if not success:
                loglines.append( ftps.lastErrorText() )
                return False, loglines
        n = ftps.GetDirCount()
        if n < 0:
            loglines.append( ftps.lastErrorText() )
            return False, loglines        
        elif n == 0:
            loglines.append( 'no files in directory' )
        else:
            for i in range( 0, n ):
                filename = ftps.getFilename( i )
                if self.SETTINGS.get( 'debug' ):
                    loglines.append( 'checking file ' + filename )
                if re.search( filter, filename ):
                    localfile = os.path.join( destination, filename )
                    success = ftps.GetFile( filename, localfile )
                    if success == True:
                        loglines.append( 'downloaded %s to %s' % (filename, localfile) )
                        dlist.append( filename )
                        if self.SETTINGS.get( 'deleteafterdownload' ):
                            success = ftps.DeleteRemoteFile( filename )
                            if success:
                                loglines.append( 'deleted file %s from ftps site' % filename )
                            else:
                                loglines.extend( ['unable to delete file', ftps.lastErrorText()] ) 
                    else:
                        loglines.append( 'unable to download %s to %s' % (filename, localfile) )
                        if self.SETTINGS.get( 'debug' ):
                           loglines.append( sftp.lastErrorText() ) 
        success = ftps.Disconnect()
        if not success and self.SETTINGS.get( 'debug' ):
            loglines.append( sftp.lastErrorText() )
        return dlist, loglines


    def Upload( self, files, origin, path='' ):
        loglines = []
        ftps, cloglines = self._connect()
        loglines.extend( cloglines )
        if not ftps:
            return False, loglines
        success = ftps.ChangeRemoteDir( path )
        if not success:
            loglines.append( ftps.lastErrorText() )
            return False, loglines
        loglines.append( 'setting destination directory to ' + path )
        fsuccess = True
        for file in files:        
            loglines.append( 'transferring file ' + file )
            filepath = os.path.join( origin, file )
            success = ftps.PutFile( filepath, file )
            if not success:
                loglines.append( ftps.lastErrorText() )
                fsuccess = False
        loglines.append( 'disconnecting from FTPS server' )
        success = ftps.Disconnect()
        if not success and self.SETTINGS.get( 'debug' ):
            loglines.append( sftp.lastErrorText() )
        return fsuccess, loglines

 
class SMB:
    def __init__( self, settings ):
        self.SETTINGS = settings

    
    def _connect( self ):
        if not smb_installed:
            return False, ['pysmb python module is not installed. Please see README.md for prequisite and install instructions.']
        try:
            conn = SMBConnection( self.SETTINGS.get( 'user' ), self.SETTINGS.get( 'auth' ), self.SETTINGS.get( 'clientname' ),
                                  self.SETTINGS.get( 'host' ), domain=self.SETTINGS.get( 'domainname', '' ),
                                  use_ntlm_v2=self.SETTINGS.get( 'usentlmv2', True ), is_direct_tcp=self.SETTINGS.get( 'isdirecttcp', True ) )
        except TypeError as e:
            return False, ['error establishing smb connection', e]
        return conn, ['smb connection established']
    
    
    def Download( self, destination, filter='', path='' ):
        loglines = []
        dlist = []
        conn, cloglines = self._connect()
        loglines.extend( cloglines )
        if not conn:
            return False, loglines
        conn.connect( self.SETTINGS.get( 'hostip' ), self.SETTINGS.get( 'port', 445 ) )
        share = self.SETTINGS.get( 'share' )
        try:
            dirlist = conn.listPath( share, path )
        except smb.smb_structs.OperationFailure as e:
            return False, ['unable to get directory listing for ' + path, str( e )]
        for file in dirlist:
            if re.search( filter, file.filename ):
                success = True
                srcpath = '/'.join( [path, file.filename] )
                dstpath = os.path.join( destination, file.filename )
                loglines.append( 'copying //%s/%s to %s' % (share, srcpath, dstpath) )
                with open( dstpath, 'wb' ) as dfile:
                    try:
                        conn.retrieveFile( share, srcpath, dfile )
                    except smb.smb_structs.OperationFailure as e:
                        success = False
                        loglines.extend( ['error reading file', str( e )] )
                if success:
                    dlist.append( file.filename )
                    if self.SETTINGS.get( 'deleteafterdownload' ):
                        try:
                            loglines.append( 'deleteing file %s from %s' % (srcpath, share) )
                            conn.deleteFiles( share, srcpath )
                        except smb.smb_structs.OperationFailure as e:
                            loglines.extend( ['error deleting file', str( e )] )    
        return dlist, loglines
                                     

    def Upload( self, files, origin, path='' ):
        loglines = []
        conn, cloglines = self._connect()
        loglines.extend( cloglines )
        if not conn:
            return False, loglines
        conn.connect( self.SETTINGS.get( 'hostip' ), self.SETTINGS.get( 'port', 445 ) )
        share = self.SETTINGS.get( 'share' )
        fsuccess = True
        try:
            conn.createDirectory( share, path )
        except smb.smb_structs.OperationFailure:
            pass # this error happens if the directory already exists
        for file in files:        
            remotefilepath = '/'.join( [path, file] )
            localfilepath = os.path.join( origin, file )
            loglines.append( 'copying %s to //%s/%s' % (localfilepath, share, remotefilepath) )
            with open( localfilepath, 'rb' ) as lfile:
                try:
                    conn.storeFile( share, remotefilepath, lfile)
                except smb.smb_structs.OperationFailure as e:
                    fsuccess = False
                    loglines.extend( ['error writing file', str( e )] )
        loglines.append( 'disconnecting from SMB server' )
        conn.close()
        return fsuccess, loglines
                          
                             
                             
                             