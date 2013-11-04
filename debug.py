#! /usr/bin/python3
import ExM

class BeidouSpecialSender(ExM.ExSender):
	"""docstring for BeidouSpecialSender"""
	def _mx_lookup(self):
		if self.domain == 'ibeidou.net':
			self.mxHosts= ('mxbiz1.qq.com','mxbiz2.qq.com')
			return
		else:
			super()._mx_lookup()

class BeidouSpecialControl(ExM.ExControl):
	def get_real_addr(self, addr):
		final= None
		try:
			final= self.resources['rcpt'].find_one({'_id':addr})['to']
			assert final
		except (KeyError, TypeError,AssertionError):
			if ExM.domain(addr) == 'ibeidou.net' or ExM.domain(addr) == 'ex.ibeidou.net':
				final= addr.replace('ex.ibeidou.net','ibeidou.net')
				ExM.logger.warn('ExControl Accepted Unknown ibeidou.net Special Address %s , Returning %s.' % (addr,final))
			else:
				ExM.logger.warn('ExControl Rejected mail RCPT TO %s.' % addr)
		else:
			ExM.logger.info('ExControl Accepted mail RCPT TO %s.' % addr)
			pass
		finally:
			return final

if __name__ == '__main__':
	try:
		BeidouSpecialControl(('localhost',8025),3,customsender= BeidouSpecialSender).start()
	except KeyboardInterrupt:
		ExM.logger.info('Got ^C. ExControl killself.')
