import os
import datetime
import sys

def est_finish(started, done, total):
    '''Return a datetime object estimating date of finishing. @param started is a datetime object when the job started, @param done is the number of currently done elements and @total is the remaining elements to do work on.'''
    assert(done <= total)
    if not total or total <= 0 or done <= 0:
        return ' -- '
    delta = datetime.datetime.now() - started
    remaining = (delta.total_seconds() * (total - done)) / float(done)
    res = datetime.datetime.now() + datetime.timedelta(seconds=remaining)
    return res.strftime('%Y-%m-%d %H:%M')

def getTerminalSize():
    '''returns terminal size as a tuple (x,y)'''
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (25, 80)
    return int(cr[1]), int(cr[0])



class ProgressBar:
    def __init__(self, minValue = 0, maxValue = 10, totalWidth=getTerminalSize()[0]):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = int(minValue)
        self.max = int(maxValue)
        self.span = self.max - self.min
        self.width = totalWidth
        self.done = 0
        self.percentDone_last = -1
        self.percentDone = 0
        self.updateAmount(0)  # Build progress bar string
        self.lastMsg = ''

    def updateAmount(self, done = 0, msg=''):
        if done < self.min:
            done = self.min

        if done > self.max:
            done = self.max

        self.done = done

        if self.span == 0:
            self.percentDone = 100
        else:
            self.percentDone = int(((self.done - self.min) * 100) / self.span)

        if self.percentDone == self.percentDone_last and self.lastMsg == msg:
            return False
        else:
            self.percentDone_last = self.percentDone

        # Figure out how many hash bars the percentage should be
        allFull = self.width - 2
        numHashes = (self.percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # build a progress bar with hashes and spaces
        self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

        # figure out where to put the percentage, roughly centered
        if not msg:
            percentString = str(self.percentDone) + "%"
        else:
            percentString = str(self.percentDone) + "%" + ' ' + msg

        percentString = '{0}% {1}'.format(str(self.percentDone),msg)

        percentPlace = len(self.progBar)//2 - len(percentString)//2
        if percentPlace < 0:
            percentPlace = 0

        # slice the percentage into the bar
        self.progBar = self.progBar[0:percentPlace] + percentString[:allFull] + self.progBar[percentPlace+len(percentString):]
        return True

    def __call__(self, amt, msg='', force=False):
        if self.updateAmount(amt, msg):
            sys.stdout.write(str(self))
            if sys.stdout.isatty():
                sys.stdout.write("\r")
            else:
                sys.stdout.write("\n")
            sys.stdout.flush()


    def __str__(self):
        return str(self.progBar)


