function fetchPisos(barcoId) {
    const conteId = document.getElementById('conte_id').value;
    fetch(`/contenedor/${conteId}`)
        .then(response => response.json())
        .then(contenedor => {
            const capacidadContenedor = contenedor.capacidad;
            fetch(`/pisos/${barcoId}`)
                .then(response => response.json())
                .then(data => {
                    let pisoSelect = document.getElementById('piso_id');
                    pisoSelect.disabled = false;
                    pisoSelect.innerHTML = '<option value="" selected disabled>Selecciona un piso disponible</option>';
                    data.forEach(piso => {
                        let option = document.createElement('option');
                        option.value = piso.id;
                        option.text = `Piso ${piso.numero_piso} - Capacidad: ${piso.capacidad} KG (Ocupada: ${piso.capacidad_ocupada} KG)`;
                        if (piso.capacidad - piso.capacidad_ocupada < capacidadContenedor) {
                            option.disabled = true;
                        }
                        pisoSelect.appendChild(option);
                    });
                });
        });
}


//Script para envios


function actualizarPuertosDestino() {
    // Obtener el valor del puerto de origen seleccionado
    var puertoOrigenId = document.getElementById('puertoO').value;

    // Obtener el selector de puerto de destino
    var puertoDestinoSelect = document.getElementById('puertoD');

    // Obtener todas las opciones de puerto de destino
    var opcionesDestino = puertoDestinoSelect.options;

    // Habilitar todas las opciones primero
    for (var i = 0; i < opcionesDestino.length; i++) {
        opcionesDestino[i].disabled = false;
    }

    // Deshabilitar la opción que coincide con el puerto de origen
    for (var i = 0; i < opcionesDestino.length; i++) {
        if (opcionesDestino[i].value === puertoOrigenId) {
            opcionesDestino[i].disabled = true;
        }
    }
}

function addDaysToDate(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function formatDateToInput(date) {
    const year = date.getFullYear();
    const month = ('0' + (date.getMonth() + 1)).slice(-2);
    const day = ('0' + date.getDate()).slice(-2);
    return `${year}-${month}-${day}`;
}

document.getElementById('fecha_salida').addEventListener('change', function() {
    const fechaSalida = new Date(this.value);
    const fechaLlegadaInput = document.getElementById('fecha_llegada');
    const fechaMinLlegada = addDaysToDate(fechaSalida, 20);

    // Establece la fecha mínima permitida para la fecha de llegada
    const fechaMinLlegadaFormatted = formatDateToInput(fechaMinLlegada);
    fechaLlegadaInput.min = fechaMinLlegadaFormatted;

    // Establece la fecha de llegada a la fecha mínima
    fechaLlegadaInput.value = fechaMinLlegadaFormatted;
});

function capitalizeWords(str) {
    return str
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}


function updateTable(barcoId) {
    const tablaPedidos = document.getElementById('tabla_pedidos');
    const tbody = tablaPedidos.querySelector('tbody');
    console.log('Fetching pedidos for barcoId:', barcoId); 
    fetch(`/get_pedidos/${barcoId}`)
        .then(response => response.json())
        .then(pedidos => {
            tbody.innerHTML = ''; // Limpiar tabla existente
            if (pedidos.length > 0) {
                tablaPedidos.classList.remove('d-none'); // Mostrar tabla si hay datos
                pedidos.forEach(pedido => {
                    let row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${pedido.id}</td>
                        <td>M-${pedido.numeroc}</td>
                        <td>${capitalizeWords(pedido.contenido)}</td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                tablaPedidos.classList.add('d-none'); // Ocultar tabla si no hay datos
            }
        });
}