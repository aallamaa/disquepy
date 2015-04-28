#
# Copyright (c) 2015, Abdelkader ALLAM <abdelkader.allam at gmail dot com>
# All rights reserved.
#
# This source also contains source code from Disque
# developped by Salvatore Sanfilippo <antirez at gmail dot com>
# available at http://github.com/antirez/disque
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of Disque nor the names of its contributors may be used
#      to endorse or promote products derived from this software without
#      specific prior written permission.
# 
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
# 

import socket
import os
import pickle
import time
import urllib2
import threading
import random
import json
from pkg_resources import resource_string
import __builtin__

redisCommands=None

def reloadCommands(url):
    global redisCommands
    try:
        u=urllib2.urlopen(url)
        redisCommands=json.load(u)
    except urllib2.HTTPError:
        raise(Exception("Error unable to load commmands json file"))


if "urlCommands" in dir(__builtin__):
    reloadCommands(__builtin__.urlCommands)


if not redisCommands:
    try:
        redisCommands=json.loads(resource_string(__name__,"commands.json"))
    except IOError:
        raise(Exception("Error unable to load commmands json file"))

    
class DisqueError(Exception):
    pass

class NodeError(Exception):
    pass


cmdmap={"del":"delete","exec":"execute"}

class MetaDisque(type):
       
       def __new__(metacls, name, bases, dct):
        def _wrapper(name,redisCommand,methoddct):
            
            runcmd="runcmd"

            def _rediscmd(self, *args):
                return methoddct[runcmd](self, name, *args)

            _rediscmd.__name__= cmdmap.get(name.lower(),str(name.lower().replace(" ","_")))
            _rediscmd.__redisname__= name
            _rediscmd._json = redisCommand
            if redisCommand.has_key("summary"):
                _doc = redisCommand["summary"]
                if redisCommand.has_key("arguments"):
                    _doc+="\nParameters:\n"
                    for d in redisCommand["arguments"]:
                        _doc+="Name: %s,\tType: %s,\tMultiple parameter:%s\n" % (d["name"],d["type"],d.get("multiple","False"))             
                _rediscmd.__doc__  = _doc
            _rediscmd.__dict__.update(methoddct[runcmd].__dict__)
            return _rediscmd

        if name != "Disque":
            return type.__new__(metacls, name, bases, dct)

        newDct = {}
        for k in redisCommands.keys():
            newDct[cmdmap.get(k.lower(),str(k.lower().replace(" ","_")))]= _wrapper(k,redisCommands[k],dct)
        newDct.update(dct)
        return type.__new__(metacls, name, bases, newDct)



class Disque(threading.local):
    """
    class providing a client interface to Disque
    """
    __metaclass__ = MetaDisque
 

    def __init__(self,host="localhost",port=7711,password=None,timeout=None,safe=False):
        self.host=host
        self.port=port
        self.timeout=timeout
        self.password=password
        self.safe=safe
        self.safewait=0.1
        self.Nodes=[Node(host,port,password,timeout)]
        self.transaction=False
        self.subscribed=False

    def listen(self,todict=False):
        while self.subscribed:
            r = self.Nodes[0].parse_resp()
            if r[0] == 'unsubscribe' and r[2] == 0:
                self.subscribed = False
            if todict:
                if r[0]=="pmessage":
                    r=dict(type=r[0],pattern=r[1],channel=r[2],data=r[3])
                else:
                    r=dict(type=r[0],pattern=None,channel=r[1],data=r[2])
            yield r


    def runcmd(self,cmdname,*args):
        #cluster implementation to come soon after antirez publish the first cluster implementation
        if cmdname in ["MULTI","WATCH"]:
            self.transaction=True
        if self.safe and not self.transaction and not self.subscribed:
            try:
                return self.Nodes[0].runcmd(cmdname,*args)
            except NodeError:
                time.sleep(self.safewait)

        if cmdname in ["DISCARD","EXEC"]:
            self.transaction=False
        try:
            if cmdname in ["SUBSCRIBE","PSUBSCRIBE","UNSUBSCRIBE","PUNSUBSCRIBE"]:
                self.Nodes[0].sendcmd(cmdname,*args)
                rsp = self.Nodes[0].parse_resp()
            else:
                rsp = self.Nodes[0].runcmd(cmdname,*args)
            if cmdname in ["SUBSCRIBE","PSUBSCRIBE"]:
                self.subscribed = True
            return rsp
        except NodeError as e:
            self.transaction=False
            self.subscribed=False
            raise NodeError(e)


    def runcmdon(self,node,cmdname,*args):
        return self.node.runcmd(cmdname,*args)


    
class Node(object):
    """
    Manage TCP connections to a redis node
    """

    def __init__(self,host="localhost",port=6379,password=None,timeout=None):
        self.host=host
        self.port=port
        self.timeout=timeout
        self.password=password
        self._sock=None
        self._fp=None

    def connect(self):
        if self._sock:
            return

        addrinfo = socket.getaddrinfo(self.host, self.port)
        addrinfo.sort(key=lambda x: 0 if x[0] == socket.AF_INET else 1)
        family, _, _, _, _ = addrinfo[0]

        sock = socket.socket(family, socket.SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(self.timeout)
            self._sock = sock
            self._fp = sock.makefile('r')

        except socket.error as msg:
            if len(msg.args)==1:
                raise NodeError("Error connecting %s:%s. %s." % (self.host,self.port,msg.args[0]))
            else:
                raise NodeError("Error %s connecting %s:%s. %s." % (msg.args[0],self.host,self.port,msg.args[1]))

        finally:
            if self.password:
                if not self.runcmd("auth",self.password):
                    raise DisqueError("Authentication error: Invalid password")

    def disconnect(self):
        if self._sock:
            try:
                self._sock.close()
            except socket.error:
                pass
            finally:
                self._sock=None
                self._fp=None
        
    def read(self,length):
        try:
            return self._fp.read(length)
        except socket.error as msg:
            self.disconnet()
            if len(msg.args)==1:
                raise NodeError("Error connecting %s:%s. %s." % (self.host,self.port,msg.args[0]))
            else:
                raise NodeError("Error %s connecting %s:%s. %s." % (msg.args[0],self.host,self.port,msg.args[1]))
       

    def readline(self):
        try:
            return self._fp.readline()
        except socket.error as msg:
            self.disconnect()
            if len(msg.args)==1:
                raise NodeError("Error connecting %s:%s. %s." % (self.host,self.port,msg.args[0]))
            else:
                raise NodeError("Error %s connecting %s:%s. %s." % (msg.args[0],self.host,self.port,msg.args[1]))


    def sendline(self,message):
        self.connect()
        try:
            self._sock.send(message+"\r\n")
        except socket.error as msg:
            self.disconnect()
            if len(msg.args)==1:
                raise NodeError("Error connecting %s:%s. %s." % (self.host,self.port,msg.args[0]))
            else:
                raise NodeError("Error %s connecting %s:%s. %s." % (msg.args[0],self.host,self.port,msg.args[1]))


    def sendcmd(self,*args):
        args2=args[0].split()
        args2.extend(args[1:])
        cmd=""
        cmd+="*%d" % (len(args2))
        for arg in args2:
            cmd+="\r\n"
            cmd+="$%d\r\n" % (len(str(arg)))
            cmd+=str(arg)
        self.sendline(cmd)
    

    def parse_resp(self):
        resp = self.readline()
        if not resp:
            # resp empty what is happening ? to be investigated
            return None
        if resp[:-2] in ["$-1","*-1"]:
            return None
        fb,resp=resp[0],resp[1:]
        if fb=="+":
            return resp[:-2]
        if fb=="-":
            raise DisqueError(resp)
        if fb==":":
            return int(resp)
        if fb=="$":
            resp=self.read(int(resp))
            self.read(2)
            return resp
        if fb=="*":
            return [self.parse_resp() for i in range(int(resp))]
        
    def runcmd(self,cmdname,*args):
        self.sendcmd(cmdname,*args)
        return self.parse_resp()



