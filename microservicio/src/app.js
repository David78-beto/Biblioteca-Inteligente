import { timingSafeEqual } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';

import express from 'express';
import { rateLimit } from 'express-rate-limit';
import { Server } from 'socket.io';
import swaggerUi from 'swagger-ui-express';

import { ErrorServicio } from './errores.js';

const documentoOpenApi = JSON.parse(readFileSync(new URL('../openapi.json', import.meta.url), 'utf-8'));

const LIMITE_POR_DEFECTO = 3;
const LIMITE_MAXIMO = 5;

function tokenValido(recibido, esperado) {
  if (!esperado || typeof recibido !== 'string') return false;
  const a = Buffer.from(recibido);
  const b = Buffer.from(esperado);
  return a.length === b.length && timingSafeEqual(a, b);
}

function leerLimite(valor) {
  if (valor === undefined) return LIMITE_POR_DEFECTO;
  if (!Number.isInteger(valor) || valor < 1 || valor > LIMITE_MAXIMO) {
    throw new ErrorServicio(400, `limite debe ser un entero entre 1 y ${LIMITE_MAXIMO}.`);
  }
  return valor;
}

function leerId(valor, campo = 'libroId') {
  if (!Number.isInteger(valor) || valor < 1) {
    throw new ErrorServicio(400, `${campo} debe ser un entero positivo.`);
  }
  return valor;
}

function leerTexto(valor, campo, minimo, maximo) {
  const texto = typeof valor === 'string' ? valor.trim() : '';
  if (texto.length < minimo || texto.length > maximo) {
    throw new ErrorServicio(400, `${campo} debe tener entre ${minimo} y ${maximo} caracteres.`);
  }
  return texto;
}

export function crearApp({ catalogo, recomendador, servicioToken, origenWeb, peticionesPorMinuto = 20 }) {
  const app = express();
  const servidor = createServer(app);
  const io = new Server(servidor, { cors: { origin: origenWeb || false } });

  app.set('trust proxy', 1);
  app.disable('x-powered-by');
  app.use(express.json({ limit: '10kb' }));

  const limitarIa = rateLimit({
    windowMs: 60 * 1000,
    limit: peticionesPorMinuto,
    standardHeaders: 'draft-8',
    legacyHeaders: false,
    message: { error: 'Demasiadas peticiones. Intenta de nuevo en un minuto.' },
  });

  function exigirToken(req, res, next) {
    if (!servicioToken) throw new ErrorServicio(503, 'El token de servicio no está configurado.');
    if (!tokenValido(req.get('X-Servicio-Token'), servicioToken)) {
      throw new ErrorServicio(401, 'Token de servicio inválido.');
    }
    next();
  }

  app.get('/', (req, res) => res.redirect('/docs/'));
  app.get('/health', (req, res) => res.json({ estado: 'ok', ia: recomendador.disponible }));
  app.get('/openapi.json', (req, res) => res.json(documentoOpenApi));
  app.use('/docs', swaggerUi.serve, swaggerUi.setup(documentoOpenApi, { customSiteTitle: 'API Biblioteca Inteligente' }));

  app.post('/api/recomendaciones', limitarIa, async (req, res) => {
    const libroId = leerId(req.body?.libroId);
    const limite = leerLimite(req.body?.limite);
    const libros = await catalogo.listar();
    const libro = libros.find(({ id }) => id === libroId);
    if (!libro) throw new ErrorServicio(404, 'El libro no existe en el catálogo.');
    res.json({ libroId, recomendaciones: await recomendador.recomendar(libro, libros, limite) });
  });

  app.post('/api/busqueda', limitarIa, async (req, res) => {
    const consulta = leerTexto(req.body?.consulta, 'consulta', 3, 200);
    const limite = leerLimite(req.body?.limite);
    const libros = await catalogo.listar();
    res.json({ consulta, resultados: await recomendador.buscar(consulta, libros, limite) });
  });

  app.post('/api/eventos/voto', exigirToken, (req, res) => {
    const evento = {
      libroId: leerId(req.body?.libroId),
      titulo: leerTexto(req.body?.titulo, 'titulo', 1, 200),
      votos: leerId(req.body?.votos, 'votos'),
    };
    io.emit('voto:actualizado', evento);
    res.status(202).json({ emitido: 'voto:actualizado', evento });
  });

  app.post('/api/eventos/libro', exigirToken, (req, res) => {
    const evento = {
      libroId: leerId(req.body?.libroId),
      titulo: leerTexto(req.body?.titulo, 'titulo', 1, 200),
      autor: leerTexto(req.body?.autor, 'autor', 1, 200),
    };
    catalogo.invalidar();
    io.emit('libro:nuevo', evento);
    res.status(202).json({ emitido: 'libro:nuevo', evento });
  });

  app.use((req, res) => res.status(404).json({ error: 'Ruta no encontrada.' }));

  app.use((error, req, res, next) => {
    if (res.headersSent) return next(error);
    if (error instanceof ErrorServicio) return res.status(error.estado).json({ error: error.message });
    if (error.type === 'entity.parse.failed') return res.status(400).json({ error: 'El cuerpo no es JSON válido.' });
    if (error.type === 'entity.too.large') return res.status(413).json({ error: 'El cuerpo es demasiado grande.' });
    console.error(error);
    return res.status(500).json({ error: 'Error interno del microservicio.' });
  });

  return { app, servidor, io };
}
