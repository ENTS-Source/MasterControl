from mcp.amp import amp
from flask import Blueprint, request, make_response

apiModule = Blueprint('api', __name__)

config = None

def init(incConfig):
    global config
    config = incConfig

def check_api_key():
    expectedKey = config.get("web", "api_key")
    if request.form["_apikey"] != expectedKey:
        abort(401)

def ok():
    return make_response("", 200)

@apiModule.route('/amp/refetch', methods=['POST'])
def index():
    check_api_key();
    amp.do_fetch_members()
    return ok()
