import { ErrorServicio } from './errores.js';

const DURACION_CACHE_MS = 5 * 60 * 1000;
const TIEMPO_MAXIMO_MS = 70 * 1000;

export function crearCatalogo({ apiUrl, obtener = fetch }) {
  let libros = null;
  let vence = 0;

  async function listar() {
    if (libros && Date.now() < vence) return libros;
    if (!apiUrl) throw new ErrorServicio(503, 'El catálogo de Django no está configurado.');

    try {
      const respuesta = await obtener(`${apiUrl}/api/libros/`, {
        signal: AbortSignal.timeout(TIEMPO_MAXIMO_MS),
      });
      if (!respuesta.ok) throw new Error(`Django respondió ${respuesta.status}`);
      libros = (await respuesta.json()).libros;
      vence = Date.now() + DURACION_CACHE_MS;
      return libros;
    } catch (error) {
      console.error('No se pudo leer el catálogo:', error.message);
      if (libros) return libros;
      throw new ErrorServicio(502, 'No se pudo leer el catálogo de Django.');
    }
  }

  function invalidar() {
    vence = 0;
  }

  return { listar, invalidar };
}
