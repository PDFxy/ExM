#! /usr/bin/python3
import bottle
import pymongo
from bson import ObjectId
from time import time,ctime
import re
from hashlib import sha1
from random import random

dbinfo={
	'host': 'localhost',
	'port': 27017,
	'database': 'bosp',
	'dbuname': '',
	'dbpasswd': '',
	'rcpt_coll': 'rcpts',
	'user_coll': 'users',
}

email_pattern= re.compile(r'^\S{1,128}@(\b\w+\b.)+\b\w{2,4}\b\.?$')

class FormDataError(Exception):
	"""docstring for FormDataError"""
	def __init__(self, key, estring=''):
		self.key= key
		super(FormDataError, self).__init__(key +' ' + estring)
	
class InvalidUser(Exception):
		"""docstring for InvalidUser"""
		def __init__(self, user, estring):
			self.user = user			
			super(InvalidUser, self).__init__(user+' '+estring)

def valid_email(addr):
	return True if email_pattern.match(addr) else False

def readForm():
	original=bottle.request.forms.decode()
	original=dict(original, **bottle.request.cookies.decode())
	finald={}
	tmp=[]
	for key in original:
		if key.endswith('_xs'):
			finald[key]= original.getall(key)
		else:
			finald[key]= original[key]
	return finald

def checkForm(argd, keyset):
	retd={}
	try:
		for key in keyset:
			try:
				retd[key]= argd[key]
			except KeyError:
				raise FormDataError(key,' is absent.')
			try:
				assert retd[key] or retd[key] =='' or retd[key]==[]		#<==== Maybe use Regular Expression later! 
			except AssertionError:
				raise FormDataError(key,' is invalid.')
		return retd
	except FormDataError as e:
		local={
			'type':'danger',
			'name': 'dataerr',
			'title': 'Form Data Error !',
			'content': '<strong>%s</strong>' % e ,
		}
		raise bottle.HTTPError(406,msg= bottle.template('alert.tpl',**local))

class BOSPAdmin(object):
	"""docstring for BOSPAdmin"""
	def __init__(self, dbinfo=dbinfo):
		super(BOSPAdmin, self).__init__()
		self.dbinfo = dbinfo
		self.resources= {}
		self._init_db()

	def get_mongo_conn(self):
		return self.resources['conn']
	
	def get_mongo_db(self):
		return self.resources['db']

	def _init_db(self):
		self.resources['conn']= pymongo.MongoClient(self.dbinfo['host'],self.dbinfo['port'])
		self.resources['db']= self.resources['conn'][self.dbinfo['database']]
		self.resources['users']= self.resources['db'][self.dbinfo['user_coll']]
		self.resources['rcpt']= self.resources['db'][self.dbinfo['rcpt_coll']]

	def ExM_add_rcpt(self, argd):
		argd= checkForm(argd,{'from','to','_id'})
		if valid_email(argd['from']) and valid_email(argd['to']):
			self.resources['rcpt'].remove({'bospUser': argd['_id']})
			self.resources['rcpt'].insert({'_id':argd['from'],'to':argd['to'],'bospUser': argd['_id']})
		else:
			raise ValueError('Invalid Email Address.')

	def ExM_get_rcpt(self, uid):
		return [x for x in self.resources['rcpt'].find({'bospUser':uid})]


	def add_user(self, argd):
		argd= checkForm(argd,{'passwd','_id'})
		argd['since']= time()
		argd['session']= ''
		self.resources['users'].insert(argd)
		return argd

	def get_user(self, argd, session= True):
		if session:
			argd= checkForm(argd,{'session',})
			return self.resources['users'].find_one(argd)
		else:
			argd= checkForm(argd,{'_id','passwd','salt'})
			usr= self.resources['users'].find_one({'_id':argd['_id']})
			return usr if sha1((usr['passwd']+str(argd['salt'])).encode()).hexdigest() == argd['passwd'] else None

	def start_session(self, uid):
		session= sha1(str(random()).encode('ascii')).hexdigest()
		self.resources['users'].update({'_id':uid},{'$set':{'session':session}})
		return session

bosp= BOSPAdmin()

@bottle.error(406)
@bottle.error(404)
@bottle.error(403)
@bottle.error(401)
def showError(err):
	msg= '400 Failure!'
	try:
		msg=err['msg']
	except KeyError:
		pass
	return msg

@bottle.get('/')
def welcome():
	usr= None
	try:
		usr= bosp.get_user(readForm())
	except bottle.HTTPError:
		pass
	local= {
		'user': usr,
	}
	return bottle.template('welcome.tpl', data= local)

@bottle.get('/signup')
def signupForm():
	usr= None
	try:
		usr= bosp.get_user(readForm())
	except bottle.HTTPError:
		pass
	local= {
		'user': usr,
	}
	return bottle.template('signup.tpl', data= local)

@bottle.post('/signup')
def signupAction():
	try:
		usr= bosp.add_user(readForm())
	except pymongo.errors.DuplicateKeyError:
		local={
			'type':'danger',
			'name': 'dataerr',
			'title': '',
			'content': '<strong>Duplicated Email address, use another one.</strong>' ,
		}
		raise bottle.HTTPError(406,msg= bottle.template('alert.tpl',**local))
	else:
		bottle.response.set_cookie('session',bosp.start_session(usr['_id']))

	return '<script type="text/javascript">window.location="/";</script>'

@bottle.post('/signin')
def signinAction():
	try:
		usr= bosp.get_user(readForm(),session= False)
		bottle.response.set_cookie('session',bosp.start_session(usr['_id']))
	except (KeyError, FormDataError, TypeError):
		local={
			'type':'danger',
			'name': 'dataerr',
			'title': '',
			'content': '<strong>Invalid email/password.</strong>' ,
		}
		raise bottle.HTTPError(406,msg= bottle.template('alert.tpl',**local))

	return '<script type="text/javascript">window.location="/";</script>'

@bottle.get('/signout')
def signoutAction():
	usr= bosp.get_user(readForm())
	if usr:
		bosp.start_session(usr['_id'])
	else:
		pass
	bottle.response.delete_cookie('session')
	bottle.redirect('/')

@bottle.get('/ExM/')
def ExMForm():
	usr= bosp.get_user(readForm())
	rcpt= bosp.ExM_get_rcpt(usr['_id'])
	local= {
		'user': usr,
		'ExM': rcpt[0] if rcpt else rcpt
	}
	return bottle.template('ExM.tpl', data= local)	

@bottle.post('/ExM/set')
def ExMForm():
	argd=readForm()
	usr= bosp.get_user(argd)
	try:
		bosp.ExM_add_rcpt(dict(argd,_id=usr['_id']))
	except pymongo.errors.DuplicateKeyError:
		local={
			'type':'danger',
			'name': 'dataerr',
			'title': 'This Address Is Taken',
			'content': '<strong>%s</strong> already registered by another user. Please come up with another one.' % argd['from'],
		}
		raise bottle.HTTPError(406,msg= bottle.template('alert.tpl', **local))
	else:
		local={
			'type':'success',
			'name': 'success',
			'title': 'All set',
			'content': '<strong>%s</strong> ==> <strong>%s</strong>.' % (argd['from'], argd['to']) ,
		}
		return bottle.template('alert.tpl', **local)


@bottle.route('/static/<filepath:path>')
def statics(filepath):
    return bottle.static_file(filepath, root='./static/')

if __name__ == '__main__':
	bottle.debug(True)
	bottle.run(host='0.0.0.0', port=8080)
else:
	application=bottle.app()