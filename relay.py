#! /usr/bin/python3
from ExM import ExControl
if __name__ == '__main__':
	try:
		ExControl(('do.jhxs.org',25),3).start()
	except KeyboardInterrupt:
		logger.info('Got ^C. ExControl killself.')