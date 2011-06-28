<%
    ## Return the list of emails as individual calls to callback
    import json
    from oidserver import VERSION

    # Serialize the passed arguments into a JSON token.
    _request = pageargs.get('request', {'params': {},
                            'path': ''})
    config = pageargs.get('config', {})
    error = pageargs.get('error', None)
    _callback = pageargs.get('callback',
        'navigator.id.registerVerifiedEmails')
    response = pageargs.get('response', {})
    _content = {"success": True}

    if error:
        _content['success'] = False
        _content['error'] = error
    emails = ''
    if response:
        if response.get('emails', None):
            emails = json.dumps(response.get('emails'))
            del (response['emails'])
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
        defaultCallback = '%s/%s/getCertificate' % (
            config.get('oid.login_host', 'https://localhost'),
            VERSION)
        rcallback  = pageargs.get('callback', )
    except KeyError as e:
        _content['x'] = e
        pass
    if 'operation' in pageargs:
        _content['operation'] = pageargs['operation']

    common_args = json.dumps(_content)
%>
%if emails:
${_callback}(${emails}, "${rcallback|h}", ${common_args})
%else:
<!-- no emails -->
%endif
