## ENTS MasterControl

MasterControl (or MCP) is what [ENTS](http://ents.ca) uses to control the door system. This system uses the member's fob number to allow
them access to the space depending on their status in aMember Pro (the member management software).

### Setup / Install

MasterControl is tested against Python 3.5.1 and Python 2.7.6.

#### Installing MasterControl

Python 3.5.1:

```
$ pip install virtualenv
$ virtualenv env
$ env/Scripts/pip install -r requirements.txt
$ env/Scripts/python -u mastercontrol.py
```

Python 2.7.6:

```
$ pip install virtualenv
$ virtualenv env
$ env/bin/pip install -r requirements.txt
$ env/bin/python -u mastercontrol.py
```
