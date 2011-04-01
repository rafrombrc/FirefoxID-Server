

class BaseController(object):
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

    def logged(self, request):
        return request.environ['beaker.session'].get('logged_in')
