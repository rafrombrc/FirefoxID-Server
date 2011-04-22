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

    function postEmail(s) {
        var req = new XMLHttpRequest();
        var uri = identityBaseURL + 'manage_email'
        var postArg = new FormData();
        var action = s.currentTarget.value;
        postArg.append('output', 'json');
        action.split('&').map( function(item){
            kv = item.split('=');
            postArg.append(kv[0],kv[1]);
        });
        try{
            req.open("POST", uri, false);
            req.send(postArg);
            resp = JSON.parse(req.responseText);
            if (resp.success) {
                if (s.currentTarget.classList.contains('validate')) {
                    s.currentTarget.innerHTML='Sent';
                }
                if (s.currentTarget.classList.contains('remove')) {                   
                    parent = s.currentTarget.parentNode.parentNode;
                    parent.parentNode.removeChild(parent);
                }
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
        var button;
        buttons = document.getElementsByTagName('button');
        console.debug(buttons);
        for (i = 0;button=buttons[i]; i++) {
            if (button.className == "disable") {
                button.addEventListener("click", postDisable, false)
                button.disabled = false;
            }
            if (button.className == 'unv') {
                buttons[i].addEventListener("click", postEmail, false)
            }
            if (button.className == 'go') {
                button.addEventListener("click", function (b) {
                    document.location = b.currentTarget.value;
                }, false)
            }
            if(button.className=="submit") {
                button.addEventListener("click", function(b){
                    document.getElementById(b.currentTarget.value).submit();
                }, false)
            }
            console.debug(button);
            if (button.className=="logout") {
                console.debug(button)
                button.addEventListener("click", function(b){
                   document.cookie = "beaker.session.id=0; expires=Thu, 01 Jan 1970 00:00:01 UTC; path=/"; 
                    console.debug(document.cookie);
                    document.location = document.location;
                
                }, false)
            }
        }
        console.debug(document.cookie);
    }

    document.addEventListener('load',init,true);

})()


