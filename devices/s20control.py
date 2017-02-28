import sys
import socket
import struct
import time


class orviboS20:

    port = 10000

    class UnknownPacket(Exception):
        def __init__ (self,value):
            self.value = value
        def __str__ (self):
            return repr(self.value)


    def __init__ ( self ):
        self.subscribed = None
        self.exitontimeout = False
        # TODO get a lock (file lock?) for port 10000 TODO
        # get a connection sorted
        self.sock = socket.socket (
                socket.AF_INET,    # Internet
                socket.SOCK_DGRAM    # UDP
            )
        self.sock.setsockopt ( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )    # https://stackoverflow.com/questions/11457676/python-socket-error-errno-13-permission-denied
        self.sock.bind ( ('',self.port) )

    def _settimeout ( self, timeout = None ):
        self.sock.settimeout ( timeout )    # seconds - in reality << 1 is needed, None = blocking (wait forever)

    # takes payload excluding first 4 (magic, size) bytes
    def _sendpacket ( self, payload, ip ):
        data = [ 0x68, 0x64, 0x00, len(payload)+4 ]
        data.extend ( payload )
#        print data
        self.sock.sendto ( ''.join([ struct.pack ( 'B', x ) for x in data ]), ( ip, 10000 ) )

    def _listendiscover ( self ):
        status = {
                'exit': True,
                'timeout': False,
                'detail': {},
            }
        if self.exitontimeout: status['exit'] = False    # we should wait for timeout, not just exit
        # we need to run and catch timeouts
        try:
            data,addr = self.sock.recvfrom ( 1024 )
            # check magic for a valid packet
            if data[0:2] != 'hd':
                return None
            # decode
            status['address'],status['port'] = addr
            status['detail']['length'] = struct.unpack ( '>H', data[2:4] )[0]
            status['detail']['commandid'] = struct.unpack ( '>H', data[4:6] )[0]
#            print "Length: %d" % status['detail']['length']
#            print "commandid: 0x%04x" % status['detail']['commandid']
            # then based on the lenth / command we can expect different stuff
            if status['detail']['length'] == 6 and status['detail']['commandid'] == 0x7161:
                # already got everything
                # global discovery - we probably sent this
#                print "command: Global Discovery"
                status['command'] = 'Global Discovery'
                status['exit'] = False    # expect more after this
            elif status['detail']['length'] == 18 and status['detail']['commandid'] == 0x7167:
                # discovery - we probably sent this
#                print "command: Discovery"
                status['command'] = 'Discovery'
                status['exit'] = False    # expect more after this
                # get remaining stuff
                status['detail']['dstmac'] = struct.unpack ( '6B', data[6:12] )
                status['detail']['srcmac'] = struct.unpack ( '6B', data[12:18] )
#                print "mac: %s" % ':'.join( [ '%02x' % c for c in status['detail']['dstmac']  ] )
#                print "padding: %s" % ':'.join( [ '%02x' % c for c in status['detail']['srcmac'] ] )
            elif status['detail']['length'] == 42 and ( status['detail']['commandid'] == 0x7161 or status['detail']['commandid'] == 0x7167 ):
                # returned discovery
#                print "command: Discovery (response)"
                status['command'] = 'Discovery (response)'
                # get remaining stuff
                zero = struct.unpack ( '>B', data[6:7] )[0]
                if zero != 0: sys.stderr.write ( "WARNING: [0] zero = 0x%02x\n" % zero )
                status['detail']['dstmac'] = struct.unpack ( '6B', data[7:13] )
                status['detail']['srcmac'] = struct.unpack ( '6B', data[13:19] )
                dstmacr = struct.unpack ( '6B', data[19:25] )
                srcmacr = struct.unpack ( '6B', data[25:31] )
#                print "mac: %s" % ':'.join( [ '%02x' % c for c in status['detail']['dstmac']  ] )
#                print "padding: %s" % ':'.join( [ '%02x' % c for c in status['detail']['srcmac'] ] )
                status['detail']['soc'] = data[31:37]
#                print "soc: %s" % status['detail']['soc']
                status['detail']['timer'] = struct.unpack ( 'I', data[37:41] )[0]
#                print "1900+sec: %d" % status['detail']['timer']
                status['state'] = struct.unpack ( 'B', data[41] )[0]
#                print "state: %d" % status['state']
            elif status['detail']['length'] == 24 and status['detail']['commandid'] == 0x636c:
                # returned subscription TODO separate this - we should only be looking for subscription related stuff after and not tricked by other (discovery) stuff
                status['detail']['dstmac'] = struct.unpack ( '6B', data[6:12] )
                status['detail']['srcmac'] = struct.unpack ( '6B', data[12:18] )
#                print "mac: %s" % ':'.join( [ '%02x' % c for c in status['detail']['dstmac']  ] )
#                print "padding: %s" % ':'.join( [ '%02x' % c for c in status['detail']['srcmac'] ] )
                zero = struct.unpack ( '>5B', data[18:23] )
                for i in range(5):
                    if zero[i] != 0: sys.stderr.write ( "WARNING: [1] zero[%d] = 0x%02x\n" % (i,zero) )
                status['state'] = struct.unpack ( 'B', data[23] )[0]
#                print "state: %d" % status['state']
            elif status['detail']['length'] == 23 and status['detail']['commandid'] == 0x6463:
                # returned power on/off TODO separate this - we should only be looking for subscription related stuff after and not tricked by other (discovery) stuff
                status['detail']['dstmac'] = struct.unpack ( '6B', data[6:12] )
                status['detail']['srcmac'] = struct.unpack ( '6B', data[12:18] )
#                print "mac: %s" % ':'.join( [ '%02x' % c for c in status['detail']['dstmac']  ] )
#                print "padding: %s" % ':'.join( [ '%02x' % c for c in status['detail']['srcmac'] ] )
                status['detail']['peercount'] = struct.unpack ( 'B', data[18] )    # number of peers on the network
                zero = struct.unpack ( '>4B', data[19:23] )
                for i in range(4):
                    if zero[i] != 0: sys.stderr.write ( "WARNING: [2] zero[%d] = 0x%02x\n" % (i,zero[i]) )
                # previous info said 4 bytes zero, 5th state, but on my S20 this is always zero, so assume as above 5 bytes zero, no state
            else:
                raise UnknownPacket
        except socket.timeout:
            # if we are doing timeouts then just catch it - it's probably for a reason
            status['timeout'] = True
            if self.exitontimeout: status['exit'] = True
        except UnknownPacket, e:    # TODO this should be more specific to avoid trapping syntax errors
            sys.stderr.write ( "Error: %s:\n" % e )
            sys.stderr.write ( "Unknown packet:\n" )
            for c in struct.unpack ( '%dB' % len(data), data ):
                sys.stderr.write ( "* %02x \"%s\"\n" % (c,chr(c)) )

        return status



    def listen ( self ):
        self._settimeout ( None )    # set blocking
        self.exitontimeout = False
        return self._listendiscover ()
    def discover ( self, ip, mac ):
        self._settimeout ( 2 )
        self.exitontimeout = True
#        macasbin = ''.join ( [ struct.pack ( 'B', int(x,16) ) for x in mac.split ( ':' ) ] )
#        self.sock.sendto ( 'hd\x00\x12\x71\x67'+macasbin+'      ' , ( ip, 10000 ) )
        data = [ 0x71, 0x67 ]
        data.extend ( [ int(x,16) for x in mac.split ( ':' ) ] )
        data.extend ( [ 0x20, 0x20, 0x20, 0x20, 0x20, 0x20 ] )
        self._sendpacket ( data, ip )
        data = []
        while True:
            resp = self._listendiscover ()
            data.append ( resp )
            if resp['exit']: break
        return data
    def globaldiscover ( self, ip ):
        self._settimeout ( 2 )
        self.exitontimeout = True
#        self.sock.sendto ( 'hd\x00\x06\x71\x61' , ( ip, 10000 ) )
        self._sendpacket ( [ 0x71, 0x61 ], ip )
        data = []
        while True:
            resp = self._listendiscover ()
            data.append ( resp )
            if resp['exit']: break
        return data
    def subscribe ( self, ip, mac ):
        self._settimeout ( 2 )
        self.exitontimeout = True
        data = [ 0x63, 0x6c ]
        data.extend ( [ int(x,16) for x in mac.split ( ':' ) ] )
        data.extend ( [ 0x20, 0x20, 0x20, 0x20, 0x20, 0x20 ] )
        data.extend ( [ int(x,16) for x in reversed ( mac.split ( ':' ) ) ] )
        data.extend ( [ 0x20, 0x20, 0x20, 0x20, 0x20, 0x20 ] )
        self._sendpacket ( data, ip )
        resp = self._listendiscover ()
        self.subscribed = [
                resp['address'],
                ''.join ( [ struct.pack ( 'B', x ) for x in resp['detail']['dstmac'] ] ),
#                ':'.join ( [ "%02x" % x for x in resp['detail']['dstmac'] ] )
                [ x for x in resp['detail']['dstmac'] ]
            ]
        time.sleep ( 0.01 )    # need a delay >6ms to be reliable - comands before that may be ignored
        return resp

    def _subscribeifneeded ( self, ip, mac ):
        if mac == None and self.subscribed != None:
            # already subscribed
            pass
        elif ip != None and mac != None:
            # subscribe or check existing subscription
            macasbin = ''.join ( [ struct.pack ( 'B', int(x,16) ) for x in mac.split ( ':' ) ] )
            if self.subscribed == None or self.subscribed[1] != macasbin:
                # new subscription / re-subscription
                self.subscribe ( ip, mac )
                if self.subscribed == None or self.subscribed[1] != macasbin:
                    raise    # something failed
    def poweron ( self, ip = None, mac = None ):
        self._subscribeifneeded ( ip, mac )
        # we should now be subscribed - go ahead with the power command
        data = [ 0x64, 0x63 ]
        data.extend ( self.subscribed[2] )
        data.extend ( [ 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0x00, 0x01 ] )
        self._sendpacket ( data, self.subscribed[0] )
        resp = self._listendiscover ()
#        pprint.pprint ( resp )
        return resp

    def poweroff ( self, ip = None, mac = None ):
        self._subscribeifneeded ( ip, mac )
        # we should now be subscribed - go ahead with the power command
        data = [ 0x64, 0x63 ]
        data.extend ( self.subscribed[2] )
        data.extend ( [ 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00 ] )
        self._sendpacket ( data, self.subscribed[0] )
        resp = self._listendiscover ()
#        pprint.pprint ( resp )
        return resp
