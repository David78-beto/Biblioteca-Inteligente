import { GoogleGenAI } from '@google/genai';

export const MODELO_POR_DEFECTO = 'gemini-3.5-flash-lite';

// Gemini responde 429 o 503 cuando tiene demasiada demanda; suele resolverse en segundos.
const ESTADOS_TEMPORALES = new Set([429, 500, 503]);
const ESPERAS_MS = [1000, 3000];

const pausa = (ms) => new Promise((resolver) => setTimeout(resolver, ms));

export function crearGenerador({ apiKey, modelo = MODELO_POR_DEFECTO, cliente, esperas = ESPERAS_MS }) {
  if (!apiKey && !cliente) return null;
  const gemini = cliente ?? new GoogleGenAI({ apiKey });

  return async function generar({ instrucciones, contenido, esquema }) {
    for (let intento = 0; ; intento += 1) {
      try {
        const respuesta = await gemini.models.generateContent({
          model: modelo,
          contents: contenido,
          config: {
            systemInstruction: instrucciones,
            responseMimeType: 'application/json',
            responseJsonSchema: esquema,
          },
        });
        return JSON.parse(respuesta.text);
      } catch (error) {
        if (!ESTADOS_TEMPORALES.has(error.status) || intento >= esperas.length) throw error;
        console.warn(`Gemini respondió ${error.status}; reintento ${intento + 1} de ${esperas.length}.`);
        await pausa(esperas[intento]);
      }
    }
  };
}
