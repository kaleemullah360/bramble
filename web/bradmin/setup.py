import os
import json

from flask import render_template, redirect, url_for, request, abort
from flask.ext.login import current_user
from flask.ext.mako import MakoTemplates
from flask.ext.mako import render_template as render_mako
from flaskext.bcrypt import Bcrypt

from bradmin import app, db, rest, lowpan, conf, coap, radio

bcrypt = Bcrypt(app)
mako = MakoTemplates(app)

BASE_URL = "https://api.lowpan.com/api/br/"

def kwSet(dbFile, **kwargs):
    """ Set attributes in kword args to target file """
    d = json.loads(db.get(dbFile))
    for a in kwargs:
        d[a] = kwargs[a]
        db.store(dbFile, json.dumps(d, sort_keys=True, indent=4))

@app.route("/", methods=['GET', 'POST'])
def brSetup():
    if request.method == 'GET':
        return render_mako('brSetup.html', url=BASE_URL)

    elif request.method == 'POST':

	baseurl = BASE_URL
        br = {}
	if request.form['url'] != '':
	    baseurl = request.form['url']
	    if baseurl[-1] != '/':
	        baseurl = baseurl + '/'
            br = lowpan.getBRInfo(request.form['eui'], request.form['brkey'], baseurl)
        else: 
            br = lowpan.getBRInfo(request.form['eui'], request.form['brkey'])

        lowpan.createDefaultConf()
        lowpanConf = json.loads(db.get('conf/lowpan'))
        lowpanConf['eui'] = request.form['eui']
        lowpanConf['password'] = request.form['brkey']
        lowpanConf['url'] = baseurl + request.form['eui']

        db.store('conf/lowpan', json.dumps(lowpanConf))
        db.store('conf/lowpan.factory', json.dumps(lowpanConf))
        db.store('conf/br', json.dumps(br))
        db.store('conf/br.factory', json.dumps(br))

        lowpan.syncConfig()
        lowpan.updateGogoc()

        # set the radio's serial (which also sets the eui)
        try:
            radio.setSerial(br['m12serial'])
        except KeyError:
            print "Warning: no m12 serial number set"
        # change root password
        os.system('echo "root:%s" | chpasswd' % (br['pin']))
        # also set login password to pin
        conf['password'] = bcrypt.generate_password_hash(br['pin'])
        db.store('conf/bradmin', json.dumps(conf, sort_keys=True, indent=4))
        db.store('conf/bradmin.factory', json.dumps(conf, sort_keys=True, indent=4))
        # set the hostname
        os.system('hostnamectl set-hostname br12-%s' % (lowpanConf['eui']))

        return "Now you need to restart BRamble"
