<%
    ## This page works in co-ordination with the front end code. It is invoked
    ## when the ouput form is set to "json".
    import json

    # Serialize the passed arguments into a JSON token.
    _request = pageargs.get('request', {'params': {},
                            'path': ''})
    _content = {"success": True}
    if 'error' in pageargs:
        _content['success'] = False
        _content['error'] = pageargs.get('error', {})
    if 'response' in pageargs:
        try:
            for key in pageargs['response'].keys():
                _content[key] = pageargs['response'][key]
        except AttributeError as e:
            pass
    _content['sid'] = ''
    _content['operation'] = ''
    _callback = ''
    try:
        path = request.path
        path = path[path.rfind('/') + 1:]
        _content['operation'] = path
        _content['sid'] = _request.params.get('sid', '')
        _callback  = _request.params.get('callback', '')
    except KeyError as e:
        _content['x'] = e
        pass
    if 'operation' in pageargs:
        _content['operation'] = pageargs['operation']
    _serialized = json.dumps(_content)
    if len(_callback) > 0:
        _serialized = "%s(%s)" % (_callback, _serialized)

%>
${_serialized}
