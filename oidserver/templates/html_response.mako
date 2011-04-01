<%
##    This page works in co-ordination with the front end code. It is invoked
##    when the ouput form is set to "json".
    import json

    # Serialize the passed arguments into a JSON token.
    _request = pageargs.get('request',{'params':{},
                            'path':''})
    _content = {"success": True}
    if 'error' in pageargs:
        _content['success'] = False
    if 'response' in pageargs:
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
window.opener.postMessage(JSON.stringify(${_serialized}),"*")
</script>
</body>
</html>
