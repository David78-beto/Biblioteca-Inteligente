import assert from 'node:assert/strict';
import { test } from 'node:test';

import { crearGenerador } from '../src/ia.js';

function clienteFalso(respuestas) {
  const llamadas = [];
  return {
    llamadas,
    models: {
      generateContent: async (peticion) => {
        llamadas.push(peticion);
        const siguiente = respuestas.shift();
        if (siguiente instanceof Error) throw siguiente;
        return { text: JSON.stringify(siguiente) };
      },
    },
  };
}

const errorConEstado = (status) => Object.assign(new Error(`HTTP ${status}`), { status });
const peticion = { instrucciones: 'Reglas', contenido: '{}', esquema: { type: 'object' } };

test('envía el modelo, las instrucciones y el esquema JSON', async () => {
  const cliente = clienteFalso([{ resultados: [] }]);
  const generar = crearGenerador({ cliente, modelo: 'modelo-de-prueba', esperas: [] });
  assert.deepEqual(await generar(peticion), { resultados: [] });
  const { model, config } = cliente.llamadas[0];
  assert.equal(model, 'modelo-de-prueba');
  assert.equal(config.systemInstruction, 'Reglas');
  assert.equal(config.responseMimeType, 'application/json');
  assert.deepEqual(config.responseJsonSchema, { type: 'object' });
});

test('reintenta cuando Gemini tiene alta demanda', async () => {
  const cliente = clienteFalso([errorConEstado(503), errorConEstado(429), { resultados: [{ id: 6 }] }]);
  const generar = crearGenerador({ cliente, esperas: [0, 0] });
  assert.deepEqual(await generar(peticion), { resultados: [{ id: 6 }] });
  assert.equal(cliente.llamadas.length, 3);
});

test('se rinde después de agotar los reintentos', async () => {
  const cliente = clienteFalso([errorConEstado(503), errorConEstado(503), errorConEstado(503)]);
  const generar = crearGenerador({ cliente, esperas: [0, 0] });
  await assert.rejects(() => generar(peticion), { status: 503 });
  assert.equal(cliente.llamadas.length, 3);
});

test('no reintenta errores permanentes, como una clave inválida', async () => {
  const cliente = clienteFalso([errorConEstado(400), { resultados: [] }]);
  const generar = crearGenerador({ cliente, esperas: [0, 0] });
  await assert.rejects(() => generar(peticion), { status: 400 });
  assert.equal(cliente.llamadas.length, 1);
});
