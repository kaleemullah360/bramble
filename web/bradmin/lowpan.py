import os
import json
import urllib2
import md5
import string
import time
import urllib2
from random import choice

from flask import render_template, redirect, url_for, request, jsonify
from flask.ext.login import login_required
from flask.ext.mako import MakoTemplates
from flask.ext.mako import render_template as render_mako
from flaskext.bcrypt import Bcrypt

from bradmin import app, db, conf, rest

bcrypt = Bcrypt(app)
mako = MakoTemplates(app)

def getBRInfo(eui, key, baseurl="https://api.lowpan.com/api/br/"):
    """ return True if eui and br key combination are ok """
    data = json.dumps({ "apikey": key })
    url = baseurl + eui
    req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(req)
    response = json.loads(f.read())
    f.close()
    return response['device']

def createDefaultConf():
    lowpanConf = { 
        "url" : None, 
        "password" : None,
        "realm" : "lowpan",
        "gogo-conf": "/etc/gogoc"
        }
    db.store('conf/lowpan', json.dumps(lowpanConf, sort_keys=True, indent=4))

def init():
    print "lowpan init"

    # make a default lowpan config
    lowpanConf = None
    try:
        lowpanConf = json.loads(db.get('conf/lowpan'))    
    except IOError:
        # load default config
        createDefaultConf()

    if (lowpanConf['url'] != None) and (lowpanConf['password'] != None):
        try:
            syncConfig()
        except urllib2.HTTPError:
            print "Couldn't connect to lowpan"

def syncConfig():
    """ get BR information from Lowpan """
    lowpanConf = json.loads(db.get('conf/lowpan'))

    try:
        response = urllib2.urlopen( lowpanConf['url'] + '?apikey=' + lowpanConf['password'] )
        brConf = json.loads(response.read())
    except:
        print "couldn't connect to lowpan"
        return

    db.store('conf/br', json.dumps(brConf, sort_keys=True, indent=4))
    

    # create gogoc.conf
    distro = 'arch'
    try:
       with open('/etc/apt/sources.list') as f: 
           distro = 'debian'
    except IOError as e:
        pass

    # search for lowpan.json config file
    search = ['/etc/gogoc', '/var/cache/bradmin', '/etc/lowpan', '/usr/local/etc/lowpan', '.']

    gogotmpl = None
    for s in search:
        try:
            gogotmpl = open(s + '/gogoc.conf.tmpl.' + distro, 'r')
        except IOError:
            pass

    if gogotmpl is None:
        print "couldn't open gogoc template"
        return

    # generate a tunnel password
    chars = string.letters + string.digits 
    length = 24
    tunpassword = ''.join(choice(chars) for _ in range(length))
    m = md5.new()
    try:
        m.update(brConf['device']['eui'])
        m.update(':' + lowpanConf['realm'] + ':') 
    except KeyError:
        print "invalid config"
        return
    m.update(tunpassword)
    tunpasshash = m.hexdigest()

    data = json.dumps( { "passhash": tunpasshash } )
    headers = { "Content-type": "application/json" }
    req = urllib2.Request(lowpanConf['url'] + '/tunnel/passhash?apikey=' + lowpanConf['password'], data, headers)
    resp = urllib2.urlopen(req)

    #print "sending passhash " + tunpasshash + " for password " + tunpassword

    gogo = ''
    gogo = gogo + "userid=%s\n" % (brConf['device']['eui'])
    gogo = gogo + "passwd=%s\n" % (tunpassword)
    gogo = gogo + "server=%s\n" % (brConf['device']['tunnel']['uri'])
    gogo = gogo + "\n"
    gogo = gogo + gogotmpl.read()
    
    os.system('mkdir -p %s' % (lowpanConf['gogo-conf']))
    out = open(lowpanConf['gogo-conf'] + '/gogoc.conf', 'w')
    out.write(gogo)

    os.system('systemctl restart gogoc')

    time.sleep(5)
