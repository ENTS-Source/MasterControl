from mcp.amp import amp
from flask import Blueprint

apiModule = Blueprint('api', __name__)

@apiModule.route('/test')
def index():
    amp.do_fetch_members()
    return 'done'
