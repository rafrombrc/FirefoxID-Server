<%
    ## This page works in co-ordination with the front end code. It is invoked
    ## when the ouput form is set to "json".
    import json

    # Serialize the passed arguments into a JSON token.
    _request = pageargs.get('request', {'params': {},
                            'path': ''})
    error = pageargs.get('error', None)
    response = pageargs.get('response', None)
    _content = {"success": True}
    if error:
        _content['success'] = False
        _content['error'] = error

    if response:
        try:
            for key in response.keys():
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
