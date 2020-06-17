function get_prefix(obj){
    return obj.name.substr(0, obj.name.indexOf(obj.getAttribute('data-name')) - 1);
}


function update_form(obj) {
    var xhttp = new XMLHttpRequest();
    xhttp.responseType = 'json';
    xhttp.timeout = 5000; // time in milliseconds
    xhttp.ontimeout = function (e) {
        // XMLHttpRequest timed out. Do something here.
        console.log('bad timeout');
    };
    xhttp.onreadystatechange = function () {
        if (this.readyState === 4) {
            if (this.status && this.status === 200) {
                // handle a successful response
                console.log('200: Ok');
                console.log(this.response);
                const form = this.response;
                for (var key in form) {
                    // console.log(document.getElementById(`${key}`));
                    document.getElementById(`${key}`).parentElement.innerHTML = form[key];
                }
            } else {
                // handle a non-successful response
                console.log('500: Bad');
                console.log(obj.getAttribute('data-url'));
            }
        }
    };
    var data = new FormData(obj.form);
    data.append('prefix', get_prefix(obj));
    data.append('active_field', obj.getAttribute('data-name'));
    xhttp.open(obj.form.method, obj.getAttribute('data-url'), true);
    xhttp.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhttp.send(data);
}
