function actualizarPeso() {
    const tipoContenedor = document.getElementById('tamano').value;
    const pesoMaximoInput = document.getElementById('capacidad');
    let pesoMaximo;

    switch(tipoContenedor) {
        case 'Pequeño (General Cargo Ships)':
            pesoMaximo = 100000;
            break;
        case 'Panamax':
            pesoMaximo = 180000;
            break;
        case 'Post-Panamax':
            pesoMaximo = 220000;
            break;
        case 'Ultra Large Container Vessels':
            pesoMaximo = 260000;
            break;
        default:
            pesoMaximo = '';
    
    }

    pesoMaximoInput.value = pesoMaximo;
}

$(document).ready(function(){
    $('#matricula').on('input', function(){
        var numero = $(this).val();
        if (numero.length == 6) {
            $.ajax({
                url: '/check_barco_number',
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

function deleteBar(barco_id) {
    $.ajax({
        url: '/delete_barco/' + barco_id,
        type: 'DELETE',
        success: function(response) {
            if (response.success)
                window.location.href = '/embarcaciones';
        }
    });
}
