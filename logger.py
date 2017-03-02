MSG_INFO    = 0x01
MSG_WARNING = 0x02
MSG_ERROR   = 0x04
MSG_VERBOSE = 0x08
MSG_ALL     = MSG_INFO | MSG_WARNING | MSG_ERROR | MSG_VERBOSE

def logi(msg):
    print("[INFO] " + msg)
def logv(msg):
    print("[VERBOSE] " + msg)
def logw(msg):
    print("[WARNING] " + msg)
def loge(msg):
    print("[ERROR] " + msg)

class Logger(object):
    def __init__(self):
        self.logger_level = MSG_ALL
    def info(self, msg):
        if self.logger_level & MSG_INFO:
            logi(msg)
    def warning(self, msg):
        if self.logger_level & MSG_WARNING:
            logw(msg)
    def error(self, msg):
        if self.logger_level & MSG_ERROR:
            loge(msg)
    def verbose(self, msg):
        if self.logger_level & MSG_VERBOSE:
            logv(msg)
