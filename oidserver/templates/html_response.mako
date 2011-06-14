<%
##    This page works in co-ordination with the front end code. It is invoked
##    when the ouput form is set to "json".
    import json

    # Serialize the passed arguments into a JSON token.
    _request = pageargs.get('request',{'params': {},
                            'path': ''})
    callback = pageargs.get('callback', 'window.opener.postMessage')
    _content = {"success": True}
    error = pageargs.get('error', None)
    response = pageargs.get('response', None)
    if error:
        _content['success'] = False
    if response:
        try:
            for key in pageargs['response'].keys():
                _content[key] = pageargs['response'][key];
        except AttributeError as e:
            pass
    _content['sid'] = ''
    _content['operation'] = ''
    try:
        path = request.path
        path = path[path.rfind('/')+1:]
        _content['operation'] = path
    except AttributeError as e:
        pass
    if 'operation' in pageargs:
        _content['operation'] = pageargs['operation']
    _serialized = json.dumps(_content);
%>
<html>
<body>
<script>
${callback}(JSON.stringify(${_serialized}),"*")
</script>
</body>
</html>
