function deleteUser(userId) {
    $.ajax({
        url: '/delete_user/' + userId,
        type: 'DELETE',
        success: function(response) {
            if (response.success) 
                window.location.href = '/users';  // Redirige a la lista de usuarios
       }
    });
}