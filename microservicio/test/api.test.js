import assert from 'node:assert/strict';
import { after, before, beforeEach, describe, test } from 'node:test';

import { io as conectar } from 'socket.io-client';

import { crearApp } from '../src/app.js';
import { crearRecomendador } from '../src/recomendador.js';

const TOKEN = 'token-de-prueba';
const LIBROS = [
  { id: 6, titulo: 'Dune', autor: 'Frank Herbert', genero: 'Ciencia ficción', descripcion: 'Un planeta desértico.', votos: 0 },
  { id: 7, titulo: 'Fundación', autor: 'Isaac Asimov', genero: 'Ciencia ficción', descripcion: 'Un imperio galáctico.', votos: 0 },
  { id: 8, titulo: '1984', autor: 'George Orwell', genero: 'Ciencia ficción', descripcion: 'Un estado totalitario.', votos: 0 },
];

describe('microservicio', () => {
  let base;
  let instancia;
  let respuestaIa;
  let peticiones;
  let invalidaciones;

  const post = (ruta, cuerpo, cabeceras = {}) => fetch(`${base}${ruta}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...cabeceras },
    body: JSON.stringify(cuerpo),
  });

  before(async () => {
    const generar = async (peticion) => {
      peticiones.push(peticion);
      if (respuestaIa instanceof Error) throw respuestaIa;
      return respuestaIa;
    };
    instancia = crearApp({
      catalogo: { listar: async () => LIBROS, invalidar: () => { invalidaciones += 1; } },
      recomendador: crearRecomendador({ generar }),
      servicioToken: TOKEN,
      origenWeb: 'http://localhost:8000',
      peticionesPorMinuto: 1000,
    });
    await new Promise((resolver) => instancia.servidor.listen(0, '127.0.0.1', resolver));
    base = `http://127.0.0.1:${instancia.servidor.address().port}`;
  });

  after(async () => {
    await instancia.io.close();
  });

  beforeEach(() => {
    peticiones = [];
    invalidaciones = 0;
    respuestaIa = { resultados: [] };
  });

  test('health informa el estado y la IA', async () => {
    const respuesta = await fetch(`${base}/health`);
    assert.deepEqual(await respuesta.json(), { estado: 'ok', ia: true });
  });

  test('publica el documento OpenAPI y Swagger UI', async () => {
    const documento = await (await fetch(`${base}/openapi.json`)).json();
    assert.ok(documento.paths['/api/recomendaciones']);
    const docs = await fetch(`${base}/docs/`);
    assert.equal(docs.status, 200);
    assert.match(await docs.text(), /swagger-ui/);
  });

  test('recomendaciones descarta el libro actual, ids inventados y duplicados', async () => {
    respuestaIa = {
      resultados: [
        { id: 6, motivo: 'Es el mismo libro.' },
        { id: 999, motivo: 'No existe.' },
        { id: 7, motivo: 'También es una saga espacial.' },
        { id: 7, motivo: 'Repetido.' },
      ],
    };
    const respuesta = await post('/api/recomendaciones', { libroId: 6, limite: 3 });
    assert.equal(respuesta.status, 200);
    assert.deepEqual((await respuesta.json()).recomendaciones, [
      { id: 7, titulo: 'Fundación', autor: 'Isaac Asimov', genero: 'Ciencia ficción', motivo: 'También es una saga espacial.' },
    ]);
  });

  test('recomendaciones reutiliza la respuesta guardada', async () => {
    respuestaIa = { resultados: [{ id: 6, motivo: 'Parecido.' }] };
    await post('/api/recomendaciones', { libroId: 8, limite: 2 });
    await post('/api/recomendaciones', { libroId: 8, limite: 2 });
    assert.equal(peticiones.length, 1);
  });

  test('recomendaciones responde 404 si el libro no existe', async () => {
    assert.equal((await post('/api/recomendaciones', { libroId: 999 })).status, 404);
  });

  test('recomendaciones valida los datos de entrada', async () => {
    assert.equal((await post('/api/recomendaciones', { libroId: 'seis' })).status, 400);
    assert.equal((await post('/api/recomendaciones', { libroId: 6, limite: 50 })).status, 400);
  });

  test('busqueda respeta el limite y envia la consulta como datos', async () => {
    respuestaIa = { resultados: [{ id: 6, motivo: 'Ocurre en un desierto.' }, { id: 7, motivo: 'Otro.' }] };
    const respuesta = await post('/api/busqueda', { consulta: 'planeta desértico', limite: 1 });
    const cuerpo = await respuesta.json();
    assert.deepEqual(cuerpo.resultados.map(({ id }) => id), [6]);
    assert.equal(JSON.parse(peticiones[0].contenido).busqueda, 'planeta desértico');
  });

  test('busqueda rechaza consultas muy cortas', async () => {
    assert.equal((await post('/api/busqueda', { consulta: 'a' })).status, 400);
  });

  test('responde 503 cuando falla la IA, sin revelar el detalle', async () => {
    respuestaIa = new Error('clave secreta rechazada');
    const respuesta = await post('/api/busqueda', { consulta: 'un libro de misterio' });
    assert.equal(respuesta.status, 503);
    assert.doesNotMatch(JSON.stringify(await respuesta.json()), /secreta/);
  });

  test('los eventos exigen el token de servicio', async () => {
    const evento = { libroId: 6, titulo: 'Dune', votos: 1 };
    assert.equal((await post('/api/eventos/voto', evento)).status, 401);
    assert.equal((await post('/api/eventos/voto', evento, { 'X-Servicio-Token': 'otro' })).status, 401);
  });

  test('un voto publicado por Django llega al navegador por Socket.IO', async () => {
    const cliente = conectar(base, { transports: ['websocket'] });
    await new Promise((resolver) => cliente.once('connect', resolver));
    const recibido = new Promise((resolver) => cliente.once('voto:actualizado', resolver));

    const evento = { libroId: 6, titulo: 'Dune', votos: 4 };
    const respuesta = await post('/api/eventos/voto', evento, { 'X-Servicio-Token': TOKEN });

    assert.equal(respuesta.status, 202);
    assert.deepEqual(await recibido, evento);
    cliente.disconnect();
  });

  test('un libro nuevo se emite y renueva el catálogo', async () => {
    const cliente = conectar(base, { transports: ['websocket'] });
    await new Promise((resolver) => cliente.once('connect', resolver));
    const recibido = new Promise((resolver) => cliente.once('libro:nuevo', resolver));

    const evento = { libroId: 15, titulo: 'Neuromante', autor: 'William Gibson' };
    await post('/api/eventos/libro', evento, { 'X-Servicio-Token': TOKEN });

    assert.deepEqual(await recibido, evento);
    assert.equal(invalidaciones, 1);
    cliente.disconnect();
  });
});

test('sin clave de API la IA queda deshabilitada', async () => {
  const recomendador = crearRecomendador({ generar: null });
  assert.equal(recomendador.disponible, false);
  await assert.rejects(() => recomendador.buscar('misterio', LIBROS, 3), { estado: 503 });
});
