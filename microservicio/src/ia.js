import { GoogleGenAI } from '@google/genai';

export const MODELO_POR_DEFECTO = 'gemini-3.5-flash-lite';

export function crearGenerador({ apiKey, modelo = MODELO_POR_DEFECTO }) {
  if (!apiKey) return null;
  const cliente = new GoogleGenAI({ apiKey });

  return async function generar({ instrucciones, contenido, esquema }) {
    const respuesta = await cliente.models.generateContent({
      model: modelo,
      contents: contenido,
      config: {
        systemInstruction: instrucciones,
        responseMimeType: 'application/json',
        responseJsonSchema: esquema,
      },
    });
    return JSON.parse(respuesta.text);
  };
}
