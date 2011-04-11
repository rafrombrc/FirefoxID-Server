(function() {

    var identityBaseURL = 'http://localhost/1/';

    function log(m) {
        if (console.log) {
            console.log("user.id: " + m);
        }
    }

    function error(m,r) {
        log(m,r);
        document.getElementById('error').innerHTML = m;
        if (r.error && r.error.reason) {
            document.getElementById('error').innerHTML += ' '+ r.error.reason;
        }
    }
    function clearError() {
        document.getElementById('error').innerHTML = '';
    }

    function postAction(s) {
        var req = new XMLHttpRequest();
        var uri = identityBaseURL + 'remove_association'
        var action = s.currentTarget.value;
        var postArg = new FormData();
        postArg.append("output", "json");

        action.split('&').map(function(item){
            kv = item.split('=');
            postArg.append(kv[0],kv[1]);
            log (kv[0] + ' = ' + kv[1])
        });
        try {
            req.open("POST", uri, false);
            req.send(postArg);
            resp = JSON.parse(req.responseText);
            if (resp.success) {
                s.currentTarget.disabled=true;
                clearError();
            } else {
                error("I'm sorry Dave, I'm afraid I can't do that.",resp);
            }
            return resp.success
                
        } catch (ex) {
            log("Got exception " + ex + " to " + uri);
        }
        s.currentTarget.disabled = true;
        return false;
    }
        
    function init() {
        buttons = document.getElementsByClassName('disable');
        for (var i = 0;i < buttons.length; i++) {
            buttons[i].addEventListener("click", postAction, false)
            buttons[i].disabled = false;
        }
    }

    init();

})()


