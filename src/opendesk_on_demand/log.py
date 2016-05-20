# -*- coding: utf-8 -*-

"""Utility functions."""

import os.path
package_name = os.path.basename(os.path.dirname(__file__))

import logging
logger = logging.getLogger(package_name)

import syslog
syslog.openlog(package_name)

levels = {
    'logger': {
        'debug': logger.debug,
        'info': logger.info,
        'warn': logger.warn,
    },
    'syslog': {
        'debug': syslog.LOG_DEBUG,
        'info': syslog.LOG_INFO,
        'warn': syslog.LOG_WARNING,
    },
}

def log(level, *args, **kwargs):
    """Log to stdout *and* to the system console. This allows us to debug
      output both when running with the command line and when running as
      as a fusion plugin, etc.
    """

    messages = [u'{0}'.format(x) for x in args]
    messages += [u'{0}: {1}'.format(k, v) for k, v in kwargs.items()]
    for msg in messages:
        levels['logger'][level](msg)
        syslog.syslog(levels['syslog'][level], msg)

def debug(*args, **kwargs):
    return log('debug', *args, **kwargs)

def info(*args, **kwargs):
    return log('info', *args, **kwargs)

def warn(*args, **kwargs):
    return log('warn', *args, **kwargs)
