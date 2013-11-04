#! /usr/bin/python3
import smtpd
import smtplib
import threading
import sys
import DNS
import logging
from time import time,ctime
from copy import deepcopy

from pymongo import MongoClient

import asyncore


#DEBUGSTREAM = sys.stdout
logging.basicConfig(filename='./ExMlog', filemood='a', level=logging.DEBUG, format='%(asctime)s %(name)s %(threadName)s %(funcName)s %(levelname)s %(message)s')
logger= logging.getLogger('Py3-ExM')

dbinfo={
	'host': 'localhost',
	'port': 27017,
	'database': 'bosp',
	'dbuname': '',
	'dbpasswd': '',
	'rcpt_coll': 'rcpts',
	'user_coll': 'users',
}

def domain(eaddr):
	return eaddr.split('@')[-1]

def add_header(data,localaddr,peer,sender):
	addr= peer[0]
	try:
		fqdn= DNS.revlookup(addr)
	except DNS.Base.ServerError:
		fqdn= 'unknown'
	headline="Return-Path: <%s>\nReceived: from %s (%s [%s])\n\tby %s (Python3-ExM) with SMTP id %s\n\tfor <!\t!\t!ExRusr!\t!\t!>; %s +0000 (UTC)\n" % (sender,fqdn,fqdn,addr,localaddr,'NOTSET',ctime(time()))
	return headline+data

class DictWithLock(dict):
	"""docstring for DictWithLock"""
	def __init__(self, *arg,**kwarg):
		super(DictWithLock, self).__init__(*arg,**kwarg)
		self.lock = threading.Lock()

def getChannelClass(validate_func):
	class ExRChannel(smtpd.SMTPChannel):
		"""docstring for ExRChannel"""
		
		valid_rcpt = validate_func
		def setValidFunc(self,the_func):
			self.valid_rcpt= the_func
	
			
		def smtp_RCPT(self, arg):
			if not self.seen_greeting:
				self.push('503 Error: send HELO first');
				return
			print('===> RCPT', arg, file=smtpd.DEBUGSTREAM)
			if not self.mailfrom:
				self.push('503 Error: need MAIL command')
				return
			syntaxerr = '501 Syntax: RCPT TO: <address>'
			if self.extended_smtp:
				syntaxerr += ' [SP <mail-parameters>]'
			if arg is None:
				self.push(syntaxerr)
				return
			arg = self._strip_command_keyword('TO:', arg)
			address, params = self._getaddr(arg)
			if not address:
				self.push(syntaxerr)
				return
			if params:
				if self.extended_smtp:
					params = self._getparams(params.upper())
					if params is None:
						self.push(syntaxerr)
						return
				else:
					self.push(syntaxerr)
					return
			if not address:
				self.push(syntaxerr)
				return
			if not self.valid_rcpt(address):
				self.push('550 No Such User')
				return
			if params and len(params.keys()) > 0:
				self.push('555 RCPT TO parameters not recognized or not implemented')
				return
			if not address:
				self.push('501 Syntax: RCPT TO: <address>')
				return
			self.rcpttos.append(address)
			print('recips:', self.rcpttos)
			self.push('250 OK')
	return ExRChannel

def getRelayClass(validate_func,trigger_func):
	class ExRelay(smtpd.SMTPServer):
		"""docstring for ExRelay"""
		channel_class= getChannelClass(validate_func)
		trigger_send= trigger_func
	
		def __init__(self, localaddr, mailCache):
			logger.info('ExRelay start and running. %s:%d' % localaddr)
			super(ExRelay, self).__init__(localaddr,None)
			self.mailCache = mailCache
			self.fqdn=smtpd.socket.getfqdn()
	
		def process_message(self, peer, mailfrom, rcpttos, data):
			logger.info('Incoming Mail From %s ! Hands on relay servo.' % mailfrom)
			if not mailfrom or mailfrom=='<>' or (mailfrom in rcpttos):
				logger.warn('ExRelay rejected mail from %s to prevent looping mail.' % mailfrom)
				return
			data= add_header(data,self.fqdn,peer,mailfrom)
			rcpd= ''
			final=tuple()
			for rcpt in rcpttos:
				try:
					rcpt_real= validate_func(rcpt)
					assert rcpt_real
				except AssertionError:
					logger.error('ExRChannel accepted mail for %s which turned out not to be normal.' % rcpt)
					return None
				final= (mailfrom,rcpt_real,data.replace('!\t!\t!ExRusr!\t!\t!',rcpt), rcpt)
				rcpd= domain(rcpt_real)
				self.mailCache.lock.acquire()
				try:
					self.mailCache[rcpd].append(final)
				except KeyError:
					self.mailCache[rcpd]= [final,]
				finally:
					logger.info('ExRelay accepted mail from %s to %s, aka %s .' % (mailfrom,rcpt,rcpt_real))
				self.mailCache.lock.release()
			self.trigger_send()
			logger.info('Triggerd ExControl for mail sending accross all domains. Hands off from relay servo.')
			return None
	return ExRelay

class MXHostNotReachable(Exception):
	pass

class ExSender(object):
	"""docstring for ExRsender"""
	def __init__(self, domain,sendlist):
		logger.info('ExSender started. %d mails to %s.' % (len(sendlist),domain))		
		super(ExSender, self).__init__()
		self.sendlist = sendlist 
		self.domain= domain
		self.smtpsrv= None
		self.refused= []

	def _mx_lookup(self):
		try:
			self.mxHosts= tuple(y for x,y in sorted((z for z in DNS.mxlookup(self.domain) if type(z) == tuple)))
		except DNS.Base.ServerError:
			logger.error('Could not resolve MX records for %s from DNS !' % self.domain)	
			raise MXHostNotReachable

	def _connect(self):
		logger.info('Initiating SMTP connection for domain %s.' % self.domain)	
		self._mx_lookup()

		for host in self.mxHosts:
			try:
				self.smtpsrv=smtplib.SMTP(host)
			except smtpd.socket.error:
				logger.warn('Prefered MX server %s not useable, maybe another try.' % host)	
				continue
			else:
				logger.info('Prefered MX server %s connected.' % host)	
				break
		if not self.smtpsrv:
			logger.error('No MX could be reached for %s .' % self.domain)	
			raise MXHostNotReachable

	def _close(self):
		logger.info('Closing smtp connection for %s.' % self.domain)
		if self.smtpsrv:
			self.smtpsrv.close()
			self.smtpsrv= None
		else:
			pass

	def send(self):
		if not self.smtpsrv:
			self._connect()
		for item in self.sendlist:
			try:
				logger.info('Trying to send mail to %s.' % item[1])
				self.smtpsrv.sendmail(item[0],item[1],item[2])
			except smtplib.SMTPSenderRefused:
				logger.warn('Failure sending mail from %s to %s. Remote MX refused sender.' % (item[0], item[1]) )
				try:
					self.smtpsrv.rset()
				except smtplib.SMTPServerDisconnected:
					logger.warn('Remote MX cut line. Must be Tencent. What an asshole!')
					self._close()
					self._connect()
				try:
					logger.info('Giving another try with fallback sender address %s.' % item[3])
					self.smtpsrv.sendmail(item[3],item[1],item[2])
				except smtplib.SMTPException:
					logger.error('Failure sending mail from %s to %s. Remote MX refused once again. Set it to be returned' % (item[3], item[1]) )
					self.refused.append(item)
				else:
					logger.info('Mail successfully sent to %s with fallback address %s.' % (item[1], item[3]))
			except smtplib.SMTPException :
				logger.error('Failure sending mail from %s to %s. Remote MX refused recipient or whatever, nothing could be done but returning it.' % (item[0], item[1]) )
				self.refused.append(item)
			else:
				logger.info('Mail successfully sent to %s.' % item[1])
			finally:
				pass
				#self.sendlist.remove(item)
			try:
				logger.info('Performing SMTP RSET.')
				self.smtpsrv.rset()
			except smtplib.SMTPServerDisconnected:
				logger.warn('Remote MX cut line. Trying to reconnect.')
				self._close()
				self._connect()
		self._close()
		return self.refused

	def __call__(self):
		return self.send()



class ExControl(object):
	senderClass= ExSender
	
	"""docstring for ExControl"""
	def __init__(self, localaddr, maxthread, customsender=None, dbinfo=dbinfo, shared_mongo_connection=None):
		logger.info('ExControl Starting.. Maxthread %d on %s:%d.' % (maxthread,localaddr[0],localaddr[1]))
		super(ExControl, self).__init__()
		self.localaddr= localaddr
		self.dbinfo= dbinfo
		if customsender:
			self.senderClass= customsender
		else:
			pass
		self.relay= None
		self.thread_Relay= None
		self.resources= {}
		self.mailCache= {}
		self.relayCache= DictWithLock()
		self.rejected= {}
#		self.workthread= []
		self.time_to_die= False
		self.relayClass= getRelayClass(self.get_real_addr,self.trigger_send)
		self.semaphore= threading.Semaphore(maxthread)
		self.event= threading.Event()
		self.lock= threading.Lock()
		self._init_db(shared_mongo_connection)
		
	def _init_db(self,shared_conn):
		logger.info('Connecting MongoDB ')
		if shared_conn:
			self.resources['conn']= shared_conn
		else:
			self.resources['conn']= MongoClient(self.dbinfo['host'],self.dbinfo['port'])
		self.resources['db']= self.resources['conn'][self.dbinfo['database']]
		self.resources['rcpt']= self.resources['db'][self.dbinfo['rcpt_coll']]
		

	def _init_relay(self):
		logger.info('Initiating Relay Thread.')
		self.relay= self.relayClass(self.localaddr,mailCache=self.relayCache)
		self.thread_Relay= threading.Thread(name="ExRelay_smtpd",target=asyncore.loop)
		self.thread_Relay.daemon= True
		self.thread_Relay.start()

	def get_real_addr(self, addr):
		final= None
		try:
			final= self.resources['rcpt'].find_one({'_id':addr})['to']
		except (KeyError, TypeError):
			logger.warn('ExControl Rejected mail RCPT TO %s.' % addr)
		else:
#			logger.info('ExControl Accepted mail RCPT TO %s.' % addr)
			pass
		finally:
			return final

	def trigger_send(self):
		logger.info('Acknowledged Incoming mail.')
		self.event.set()

	def clear_cache(self, domain=None):
		if domain:
			del(self.mailCache[domain])
			logger.info('Cleared MailCache for %s' % domain)
		else:
			self.mailCache.clear()
			logger.info('Cleared MailCache for all domains.')

	def sender_routine(self, domain, sendlist):
		logger.info('Sender Thread for domain %s is up.' % domain)
		rejected= None
		if not sendlist:
			logger.info('Sendlist empty. Clearing Cache for %s' % domain)
#			self.clear_cache(domain)
		else:
			try:
				rejected= self.senderClass(domain,sendlist).send()
			except MXHostNotReachable:
				self.rejected[domain]= sendlist
#				self.clear_cache(domain)
				logger.error('Failure to reach %s' % domain)
			if rejected:
				logger.warn('%d Mail Rejected by %s' % (len(rejected),domain))
				try:
					pass
					#self.rejected[domain].extend(rejected )
				except KeyError:
					pass
					#self.rejected[domain]= rejected
			else:
				logger.info('Transaction for %s is over.' % domain)
		logger.info('Sender Thread for domain %s is terminating.' % domain)
		self.semaphore.release()
		return

	def terminate(self):
		logger.warn('ExControl terminating !')
		self.time_to_die= True

	def loop(self):
		logger.info('ExControl main loop starting.')
		tmpthread= None
		threadlist= []
		while True:
			if self.time_to_die:
				return
			else:
				logger.info('ExControl main loop now waits for incoming mail.')
				self.event.wait()
				logger.info('ExControl main loop is woken up.')
				self.event.clear()
				logger.info('Forking relayCache.')
				self.relayCache.lock.acquire()
				self.mailCache= self.relayCache.copy()
				logger.info('Clearing relayCache.')
				self.relayCache.clear()
				self.relayCache.lock.release()
			for domain in self.mailCache:
				tmpthread= threading.Thread(target=self.sender_routine, name=domain, args=(domain,self.mailCache[domain]))
				threadlist.append(tmpthread)
				self.semaphore.acquire()
				tmpthread.start()
			for thread in threadlist:
				logger.info('ExControl main loop awaits for thread %s to terminate.' % thread.name)
				thread.join()
			threadlist= []
			#self.clear_cache()
			logger.info('ExControl main loop cycle completed.')

	def start(self):
		self._init_relay()
		self.loop()


if __name__ == '__main__':
	try:
		ExControl(('localhost',8025),3).start()
	except KeyboardInterrupt:
		logger.info('Got ^C. ExControl killself.')
