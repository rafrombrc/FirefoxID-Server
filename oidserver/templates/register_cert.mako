<%
    ## Return the list of emails as individual calls to callback
    import json

    # Serialize the passed arguments into a JSON token.
    _request = pageargs.get('request', {'params': {},
                            'path': ''})
    error = pageargs.get('error', None)
    _callback = pageargs.get('callback',
        'navigator.id.registerVerifiedEmailCertificate')
    response = pageargs.get('response', None)
    _content = {"success": True}
    if error:
        _content['success'] = False
        _content['error'] = error

    _content['sid'] = ''
    _content['operation'] = ''
    try:
        path = request.path
        path = path[path.rfind('/') + 1:]
        _content['operation'] = path
        _content['sid'] = _request.params.get('sid', '')
        rcallback  = _request.params.get('callback', '""')
    except KeyError as e:
        _content['x'] = e
        pass
    if 'operation' in pageargs:
        _content['operation'] = pageargs['operation']

    common_args = json.dumps(_content)
%>
${_callback}("${response.get('certificate', '')}", "${response.get('callbackUrl', '')}", ${common_args})
