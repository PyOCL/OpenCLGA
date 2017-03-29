def logi(msg):
    print('[INFO] ' + msg + '\033[m')
def logv(msg):
    print('\033[1;34m[VERBOSE] ' + msg + '\033[m')
def logw(msg):
    print('\033[1;36m[WARNING] ' + msg + '\033[m')
def loge(msg):
    print('\033[1;31m[ERROR] ' + msg + '\033[m')

class Logger(object):
    MSG_INFO    = 0x01
    MSG_WARNING = 0x02
    MSG_ERROR   = 0x04
    MSG_VERBOSE = 0x08
    MSG_ALL     = MSG_INFO | MSG_WARNING | MSG_ERROR | MSG_VERBOSE
    def __init__(self):
        self.logger_level = Logger.MSG_ALL
    def info(self, msg):
        if self.logger_level & Logger.MSG_INFO:
            logi(msg)
    def warning(self, msg):
        if self.logger_level & Logger.MSG_WARNING:
            logw(msg)
    def error(self, msg):
        if self.logger_level & Logger.MSG_ERROR:
            loge(msg)
    def verbose(self, msg):
        if self.logger_level & Logger.MSG_VERBOSE:
            logv(msg)
