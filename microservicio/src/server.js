import { crearApp } from './app.js';
import { crearCatalogo } from './catalogo.js';
import { crearGenerador, MODELO_POR_DEFECTO } from './ia.js';
import { crearRecomendador } from './recomendador.js';

const {
  PORT = '3000',
  DJANGO_API_URL,
  GEMINI_API_KEY,
  GEMINI_MODEL = MODELO_POR_DEFECTO,
  ORIGEN_WEB,
  SERVICIO_TOKEN,
} = process.env;

const { servidor } = crearApp({
  catalogo: crearCatalogo({ apiUrl: DJANGO_API_URL?.replace(/\/+$/, '') }),
  recomendador: crearRecomendador({ generar: crearGenerador({ apiKey: GEMINI_API_KEY, modelo: GEMINI_MODEL }) }),
  servicioToken: SERVICIO_TOKEN,
  origenWeb: ORIGEN_WEB?.replace(/\/+$/, ''),
});

servidor.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`Microservicio en el puerto ${PORT} (IA: ${GEMINI_API_KEY ? GEMINI_MODEL : 'sin configurar'})`);
});
