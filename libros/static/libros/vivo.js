(function () {
    const servidor = document.currentScript.dataset.servidor;

    function crearTarjeta(libro) {
        const item = document.createElement('li');
        const enlace = document.createElement('a');
        enlace.className = 'tarjeta';
        enlace.href = libro.url;

        const titulo = document.createElement('strong');
        titulo.textContent = libro.titulo;
        const autor = document.createElement('span');
        autor.textContent = libro.autor + ' · ' + libro.genero;
        const motivo = document.createElement('span');
        motivo.className = 'motivo';
        motivo.textContent = libro.motivo;

        enlace.append(titulo, autor, motivo);
        item.append(enlace);
        return item;
    }

    async function cargarRecomendaciones() {
        const seccion = document.getElementById('recomendaciones');
        if (!seccion) return;
        const estado = seccion.querySelector('.estado-ia');
        try {
            const respuesta = await fetch(seccion.dataset.url);
            if (!respuesta.ok) throw new Error(String(respuesta.status));
            const { recomendaciones } = await respuesta.json();
            if (!recomendaciones.length) {
                seccion.hidden = true;
                return;
            }
            seccion.querySelector('.tarjetas').append(...recomendaciones.map(crearTarjeta));
            estado.remove();
        } catch (error) {
            estado.textContent = 'Las recomendaciones no están disponibles en este momento.';
        }
    }

    function mostrarAviso(texto) {
        const contenedor = document.getElementById('avisos-vivo');
        const aviso = document.createElement('p');
        aviso.className = 'aviso-vivo';
        aviso.textContent = texto;
        contenedor.append(aviso);
        setTimeout(function () { aviso.remove(); }, 6000);
    }

    function escucharEventos() {
        const socket = window.io(servidor, { transports: ['websocket', 'polling'] });

        socket.on('voto:actualizado', function (evento) {
            document.querySelectorAll('[data-votos-libro="' + evento.libroId + '"]').forEach(function (elemento) {
                elemento.textContent = evento.votos;
            });
            mostrarAviso('«' + evento.titulo + '» ahora tiene ' + evento.votos + (evento.votos === 1 ? ' voto.' : ' votos.'));
        });

        socket.on('libro:nuevo', function (evento) {
            mostrarAviso('Nuevo en el catálogo: «' + evento.titulo + '», de ' + evento.autor + '.');
        });
    }

    // Se carga aparte para que un microservicio dormido no retrase la página.
    const cliente = document.createElement('script');
    cliente.src = servidor + '/socket.io/socket.io.js';
    cliente.async = true;
    cliente.onload = escucharEventos;
    document.head.append(cliente);

    cargarRecomendaciones();
})();
