## ENTS MasterControl

MasterControl (or MCP) is what [ENTS](http://ents.ca) uses to control the door system. This system uses the member's fob number to allow
them access to the space depending on their status in aMember Pro (the member management software).

### Setup / Install

MasterControl is tested against Python 3.5.X.

Installing MasterControl:

```
$ pip install virtualenv
$ virtualenv env
$ env/Scripts/pip install -r requirements.txt
$ env/Scripts/python -u mastercontrol.py
```
