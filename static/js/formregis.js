function checkPasswords() {
    var password = document.getElementById('passd').value;
    var repeatPassword = document.getElementById('passd2').value;
    var submitButton = document.getElementById('btn-submit');

    if (password === repeatPassword && password.length > 0) {
        submitButton.disabled = false;
    } else {
        submitButton.disabled = true;
    }
}
function generateUsername() {
    let firstName = document.getElementById('firsname').value;
    let lastName = document.getElementById('lastname').value;

    if (firstName.length >= 3 && lastName.length >= 3) {
        let username = firstName.substring(0, 3).toLowerCase() + lastName.substring(0, 3).toLowerCase();
        validarUsuario(username)
    } else {
        document.getElementById('username').value = '';
        document.getElementById('email').value = '';
    }
}

function validarUsuario(username){
    fetch('/validarUser',{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: username})
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('username').value = data.username;
        document.getElementById('email').value = data.username + '@conte.com';
    })
    .catch(error => console.error('Error:', error));
}