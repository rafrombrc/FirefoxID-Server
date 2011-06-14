from hashlib import sha1
from services.controllers import StandardController


class BaseController(StandardController):

    # used for unit testing only
    fake_session = {}

    def __init__(self, app):
        self.app = app

    def is_type(self, request, type_):
        """ Check if the request matches a given abbreviated content type """
        # type should be "html" or "json", but folks may request a full
        # content type. Be nice and trim it to the most likely correct
        # version.
        if "/" in type_:
            type_ = type_.split("/")[1]
        if ('output' in request.params and
            type_ == request.params.get('output', '')):
            return True
        try:
            return type_ in request.accept.header_value
        except AttributeError:
            # Header is not defined or present, so return "False" since it
            # can't match "nothing"
            return False

    def get_session_uid(self, request):
        if self.fake_session:
            return self.fake_session.get('uid', None)
        return request.environ.get('beaker.session', {}).get('uid')

    def set_session_uid(self, request, uid):
        if 'beaker.session' in request.environ:
            request.environ['beaker.session']['uid'] = uid
            return True
        return False

    def gen_signature(self, uid, request):
        """ Generate a signature value (to prevent XSS) """
        remote = request.remote_addr or 'localhost'
        sbs = (remote +
            self.app.config.get('auth.secret_salt', '') +
            str(uid))
        return sha1(sbs).hexdigest()

    def check_signature(self, uid, request):
        """ Check the enclosed signature """
        if 'sig' not in request.params:
            return False
        sig_val = request.params.get('sig', '')
        if len(sig_val) < 1:
            return False
        return sig_val != self.gen_signature(uid, request)
