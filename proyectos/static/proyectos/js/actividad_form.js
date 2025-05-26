document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando formulario de actividad...');

    function calcularDuracion() {
        console.log('Calculando duración...');
        const inicioInput = document.getElementById('id_inicio');
        const finInput = document.getElementById('id_fin');
        const duracionInput = document.getElementById('id_duracion');

        console.log('Campos encontrados:', {
            inicio: inicioInput,
            fin: finInput,
            duracion: duracionInput
        });

        if (!inicioInput || !finInput || !duracionInput) {
            console.error('No se encontraron todos los campos necesarios');
            return;
        }

        const inicioValue = inicioInput.value;
        const finValue = finInput.value;

        console.log('Valores de fecha:', {
            inicio: inicioValue,
            fin: finValue
        });

        if (!inicioValue || !finValue) {
            duracionInput.value = '0';
            return;
        }

        const fechaInicio = new Date(inicioValue);
        const fechaFin = new Date(finValue);

        if (isNaN(fechaInicio.getTime()) || isNaN(fechaFin.getTime())) {
            console.error('Fechas inválidas');
            duracionInput.value = '0';
            return;
        }

        if (fechaFin < fechaInicio) {
            alert('La fecha de fin no puede ser anterior a la fecha de inicio');
            finInput.value = '';
            duracionInput.value = '0';
            return;
        }

        const diferencia = fechaFin.getTime() - fechaInicio.getTime();
        const dias = Math.floor(diferencia / (1000 * 60 * 60 * 24)) + 1;
        console.log('Días calculados:', dias);
        duracionInput.value = dias;
    }

    // Asignar eventos a los campos de fecha
    const inicioInput = document.getElementById('id_inicio');
    const finInput = document.getElementById('id_fin');

    if (inicioInput) {
        inicioInput.addEventListener('change', calcularDuracion);
        inicioInput.addEventListener('input', calcularDuracion);
    }

    if (finInput) {
        finInput.addEventListener('change', calcularDuracion);
        finInput.addEventListener('input', calcularDuracion);
    }

    // Calcular duración inicial
    calcularDuracion();

    console.log('Formulario de actividad inicializado');
});
