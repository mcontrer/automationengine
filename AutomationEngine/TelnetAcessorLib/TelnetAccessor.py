"""
Created on Mar 23, 2017

@author: smcochra

3/27/2017 - edited by smcochra
"""

import TelnetDriver
import datetime


class TelnetAccessor(object):
    """
    Encompasses Send, Expect, SendExpect, Logging to DB with Timestamp
    """

    __logger = None

    def __init__(self, debugFlag=False):
        """
        Instantiate TelnetDriver Class
        + debugFlag - enable debug messaging
        """
        self.t = TelnetDriver.TelnetDriver(debugFlag=debugFlag)

    def set_logger(self, logger):
        """
        Passes the logger object handle
        """
        self.__logger = logger

    def open_console(self, console):
        self.t.open(console)

    def close_console(self, console):
        self.t.close(console)

    def send(self, data):
        """
        Sends data to open console
        + data - string to push to socket
        """
        self.t.debug('Sending: %r' % data)
        self.t.send(data)

    def expect_old(self, matchlist, timeout=5):
        """
        Arguments -
        + matchlist - regex or list of regex's to match against
        + timeout - seconds before timeout occurs
        Returns tupple dictionary with following keys:
        + 'matchidx' - index of item matched from argument matchlist
        + 'matchobj' - MatchObject; see documentation re.MatchObject
        + 'matchtext' - raw string that pattern matched against
        + 'buffer' - buffer captured between start of expect call and timeout/match
        + 'timeout_occured' - True or False

        """
        idx, mobj, buf = self.t.expect(matchlist, timeout)

        returndict = {}

        timeout = True
        mtext = None
        if idx != -1:
            timeout = False
            # fetch entire match
            mtext = mobj.group(0)

        returndict['matchidx'] = idx
        returndict['matchobj'] = mobj
        returndict['matchtext'] = mtext
        returndict['buffer'] = buf
        returndict['timeout_occured'] = timeout

        return returndict

    def expect(self, matchlist, timeout=5):
        """
        Arguments -
        + matchlist - regex or list of regex's to match against
        + timeout - seconds before timeout occurs
        Returns tupple dictionary with following keys:
        + 'matchidx' - index of item matched from argument matchlist
        + 'matchobj' - MatchObject; see documentation re.MatchObject
        + 'matchtext' - raw string that pattern matched against
        + 'buffer' - buffer captured between start of expect call and timeout/match
        + 'bufobj' - list of dictionaries ordered with key timestamp and value list
                    of lines associated with timestamp
                    [{time1: [buffer_line_1, buffer_line_2]},
                     {time2: [buffer_line_1, buffer_line_2, ...],
                     ...,
                     ]
        + 'timeout_occured' - True or False
        + 'xtime' - execution time for expect to match

        """
        returndict = {}
        buffer = ''

        expobj = self.t.expect(matchlist, timeout)

        for dict in expobj['buffer']:
            for timestamp, line in dict.iteritems():
                buffer += '\n'.join(line)
                buffer += '\n'

        # remove last new line that was applied in excess above
        buffer = buffer[:-2]

        timeout = True
        mtext = None
        if expobj['midx'] != -1:
            timeout = False
            # fetch entire match
            mtext = expobj['mobj'].group(0)

        returndict['matchidx'] = expobj['midx']
        # returndict['matchobj'] = expobj['mobj']
        returndict['matchtext'] = mtext
        returndict['buffer'] = buffer
        returndict['bufobj'] = expobj['buffer']
        returndict['xtime'] = expobj['xtime']
        returndict['timeout_occured'] = timeout

        return returndict

    def sendexpect(self, data, matchlist, timeout=5, debug=False):
        """
        Combined send, expect;
        """
        self.send(data)
        result = self.expect(matchlist, timeout=timeout)

        if debug:
            self.__debug_expect(result)

        return result

    def sendexpect_list(self, data_list, matchlist, timeout=5, debug=False):
        """
        accepts list of commands to execute assuming same matchlist;
        returns True after successful execution
        + data_list - list of commands to run - '\r' will be appended to each command
        + matchlist - regex or list of regex's to match against
        + timeout - seconds before timeout occurs
        + debug - print out expect return values 
        """
        returnobj = []
        for data in data_list:
            result = self.sendexpect(data + '\r', matchlist, timeout, debug)
            returnobj.append(result)

        return returnobj

    def __debug_expect(self, exp_retrn_dict):
        """
        Print out expect return values
        """
        self.t.set_debug_flag(True)
        self.t.debug('------------------------------')
        for key, value in exp_retrn_dict.iteritems():
            self.t.debug('%s: %r' % (key, value))
        self.t.debug('------------------------------')

    def print_log_with_timestamps(self, expect_obj_list):
        """
        Takes list of expect return objects and prints log
        with timestamps
        """
        lastline = ''
        buflist = []
        for result in expect_obj_list:
            buflist.append(result['bufobj'])

        for cmd_dict_list in buflist:
            # connect cmd sequence lastline w/ firstline
            cmd_dict_list[0].values()[0][0] = lastline + \
                cmd_dict_list[0].values()[0][0]
            # get lastline of cmd sequence to tie to first line of next
            # sequence
            lastline = cmd_dict_list[-1].values()[0].pop()

            for bufobj in cmd_dict_list:
                for timestamp, buf_list in bufobj.iteritems():
                    for idx in range(len(buf_list)):
                        print timestamp + '\t%s' % buf_list[idx]

        # don't forget to print lastline that we are storing
        print timestamp + '\t%s' % lastline


def logmsg(msg):
    """
    Logs msg to TBD location
    """
    time = gettimestamp()
    print '%s\tlogmsg: %s' % (time, msg)


def usermsg(msg):
    """
    Logs msg to TBD location
    """
    time = gettimestamp()
    print '%s\tusermsg: %s' % (time, msg)


def gettimestamp():
    return datetime.datetime.now()


def test(console='10.31.248.147:3009'):
    usermsg('Testing User Message!')
    logmsg('Testing log Message!')

    # prints output of all expect return values
    # to provide support for debugging
    debugFlag = False

    session = TelnetAccessor(debugFlag=debugFlag)
    session.open_console(console)

    logmsg('Testing regular sendexpect...')

    #result = session.sendexpect('exit\r', '4X', debug=debugFlag)
    #result = session.sendexpect('en\r', '4X', debug=debugFlag)
    #result = session.sendexpect('skip\r', '4X', debug=debugFlag)
    #result = session.sendexpect('show media\r', '4X', timeout=5, debug=debugFlag)

    logmsg('Testing sendexpect_list...')

    data_list = ['exit', 'en', 'skip', 'show media']

    results = session.sendexpect_list(
        data_list, ['not_a_match', 'Net.*4X'], timeout=15, debug=debugFlag)

    session.print_log_with_timestamps(results)

    usermsg('Done!')
    logmsg('Done!')

# test()
