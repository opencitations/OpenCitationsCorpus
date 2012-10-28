# by http://www.garyrobinson.net/2009/10/non-blocking-raw_input-for-python.html
import signal

class AlarmException(Exception):
    pass

def alarmHandler(signum, frame):
    raise AlarmException

def nbRawInput(prompt='', timeout=5):
    signal.signal(signal.SIGALRM, alarmHandler)
    signal.alarm(timeout)
    try:
        text = raw_input(prompt)
        signal.alarm(0)
        return text
    except AlarmException:
        print '\nPrompt timeout. Continuing...'
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    return ''
