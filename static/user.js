(function() {

    var identityBaseURL = 'https://web4.dev.svc.mtv1.mozilla.com/1/';

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

    function postDisable(s) {
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

    function postResend(s) {
        var req = new XMLHttpRequest();
        var uri = identityBaseURL + 'manage_email'
        var postArg = new FormData();
        postArg.append('output', 'json');
        postArg.append('act', 'add');
        postArg.append('unv_email', s.currentTarget.value);

        try{
            req.open("POST", uri, false);
            req.send(postArg);
            resp = JSON.parse(req.responseText);
            if (resp.success) {
                s.currentTarget.innerHTML='Sent';
                return true;
            }
        } catch (ex) {
            log("Got exception " + ex + " to " + uri);
        }
        error("Sorry, I couldn't resend that email.");
        return false;
    }
        
    function init() {
        var i;
        var buttons;
        buttons = document.getElementsByClassName('disable');
        for (i = 0;i < buttons.length; i++) {
            buttons[i].addEventListener("click", postDisable, false)
            buttons[i].disabled = false;
        }
        buttons = document.getElementsByClassName('validate');
        for (i = 0;i < buttons.length; i++) {
            buttons[i].addEventListener("click", postResend, false)
        }
    }

    init();

})()


