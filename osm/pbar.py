import os
import datetime
import sys


def est_finish(started, done, total):
    '''Return a string estimating date of finishing. @param started is a datetime object when the job started, @param done is the number of currently done elements and @total is the remaining elements to do work on.'''
    assert(done <= total)
    if not total or total <= 0 or done <= 0:
        return ' -- '
    delta = datetime.datetime.now() - started
    remaining = (delta.total_seconds() * (total - done)) / float(done)
    res = datetime.datetime.now() + datetime.timedelta(seconds=remaining)
    return res.strftime('%Y-%m-%d %H:%M')


def get_terminal_size():
    '''returns terminal size as a tuple (x,y)'''
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
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

    def __init__(self, minValue = 0, maxValue = 10, totalWidth = get_terminal_size()[0]):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = int(minValue)
        self.max = int(maxValue)
        self.span = self.max - self.min
        self.width = totalWidth
        self.done = 0
        self.percentDone_last = -1
        self.percentDone = 0
        self.update_amount(0)  # Build progress bar string
        self.lastMsg = ''

    def set_max(self, max_):
        self.max = int(max_)
        self.span = self.max - self.min

    def update_amount(self, done = 0, msg=''):
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
            percentString = ' {0}% '.format(str(self.percentDone))
        else:
            percentString = ' {0}% {1} '.format(str(self.percentDone), msg)

        percentPlace = len(self.progBar)//2 - len(percentString)//2
        if percentPlace < 0:
            percentPlace = 0

        # slice the percentage into the bar
        self.progBar = self.progBar[0:percentPlace] + percentString[:allFull] + self.progBar[percentPlace+len(percentString):]
        return True

    def __call__(self, amt = -1, msg = '', force = False):
        if amt == -1:
            amt = self.done + 1
        if self.update_amount(amt, msg) or force:
            sys.stdout.write(str(self))
            if sys.stdout.isatty():
                sys.stdout.write("\r")
            else:
                sys.stdout.write("\n")
            sys.stdout.flush()

    def __str__(self):
        return str(self.progBar)

    # Support for the 'with' statement, to always include a newline
    # when the object is destroyed

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if sys.stdout.isatty():
            sys.stdout.write("\n")
            sys.stdout.flush()
