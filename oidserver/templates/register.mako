<%
    ## Return the list of emails as individual calls to callback
    import json

    # Serialize the passed arguments into a JSON token.
    _request = pageargs.get('request', {'params': {},
                            'path': ''})
    error = pageargs.get('error', None)
    _callback = pageargs.get('callback',
        'navigator.id.registerVerifiedEmail')
    response = pageargs.get('response', {})
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
%if response:
%for email in response.get('emails',[]):
${_callback}("${email}", ${rcallback}, ${common_args})
%endfor
%else:
<!-- no emails -->
%endif
