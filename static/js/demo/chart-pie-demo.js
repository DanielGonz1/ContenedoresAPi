Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

fetch('/total_pedidos')
  .then(response => response.json())
  .then(data => {
    const estados = data.map(pedido => pedido.estado);
    const cantidades = data.map(pedido => pedido.cantidad);
    var ctx = document.getElementById("myPieChart");
    var myPieChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: estados,
        datasets: [{
          data: cantidades,
          backgroundColor: ['#1cc88a', '#4e73df', '#f6c23e'], // Colores para Completados, En tránsito, Pendientes
          hoverBackgroundColor: ['#17a673', '#2e59d9', '#dda20a'],
          hoverBorderColor: "rgba(234, 236, 244, 1)",
        }],
      },
      options: {
        maintainAspectRatio: false,
        tooltips: {
          backgroundColor: "rgb(255,255,255)",
          bodyFontColor: "#858796",
          borderColor: '#dddfeb',
          borderWidth: 1,
          xPadding: 15,
          yPadding: 15,
          displayColors: false,
          caretPadding: 10,
        },
        legend: {
          display: false
        },
        cutoutPercentage: 80,
      },
    });
  })
  .catch(error => {
    console.error('Error al obtener los datos de la API:', error);
  });
