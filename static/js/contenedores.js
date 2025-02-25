$(document).ready(function(){
    $('#numero').on('input', function(){
        var numero = $(this).val();
        if (numero.length == 6) {
            $.ajax({
                url: '/check_container_number',
                type: 'GET',
                data: { numero: numero },
                success: function(response) {
                    console.log(response); 
                    if (response.exists) {
                        $('#numero-status').html('<div class="alert alert-danger" role="alert">' + response.message + '</div>');
                    } else {
                        $('#numero-status').html('<div class="alert alert-success" role="alert">' + response.message + '</div>');
                    }
                }
            });
        }else if(numero.length != 6){
            $('#numero-status').html('<div class="alert alert-warning" role="alert">' + 'El número debe tener 6 dígitos' + '</div>');
        }else {
            $('#numero-status').html('');
        }
    });
});

function deleteCont(conteid) {
    $.ajax({
        url: '/delete_conte/' + conteid,
        type: 'DELETE',
        success: function(response) {
            if (response.success)
                window.location.href = '/contenedores';
        }
    });
}

function actualizarPesoo() {
    const tipoContenedor = document.getElementById('tipo').value;
    const pesoMaximoInput = document.getElementById('peso');
    let pesoMaximo;
    switch(tipoContenedor) {
        case '20 pies':
            pesoMaximo = 24000;
            break;
        case '40 pies':
            pesoMaximo = 30480;
            break;
        case '40 pies High Cube':
            pesoMaximo = 32500;
            break;
        case '45 pies':
            pesoMaximo = 40200;
            break;
        default:
            pesoMaximo = '';
    }

    pesoMaximoInput.value = pesoMaximo;
}