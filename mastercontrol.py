import ConfigParser
import time

# Move globals to appropriate classes
global session

config = ConfigParser.ConfigParser()
config.read('config/mastercontrol.ini')

# Setup logging
# TODO

# Setup DB
# TODO

# Setup other components
# TODO

try:
    while(True):
        time.sleep(100)
except KeyboardInterrupt:
    print "^C received - shutting down server."
