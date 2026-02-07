// static/js/nsfw-validator.js
import { JigsawStack } from 'jigsawstack';

// ==========================================
// CONFIGURACIÓN
// ==========================================
const JIGSAWSTACK_API_KEY = 'sk_8fc49d46d26248a05274e78faf07893cffb62e8b25790d47e2b7ef4eca158b07ef7fbb73c69ef0e5514e8c2ac92ff956111ecbb0d7335d13cdcdb50a1525ddad024KIVF6vZqFa5acHSxde'; // ⚠️ Reemplaza con tu API key
const jigsawstack = JigsawStack({ apiKey: JIGSAWSTACK_API_KEY });

// Variable global para rastrear validez de imagen
let isImageValid = true;

// ==========================================
// VALIDACIÓN NSFW
// ==========================================
export async function validateImageNSFW(file) {
    try {
        const result = await jigsawstack.vision.nsfw_classification({
            image: file
        });
        
        console.log('Respuesta JigsawStack:', result);
        
        // Estructura típica de respuesta:
        // { is_nsfw: boolean, confidence: number, categories: {...} }
        
        return {
            isValid: !result.is_nsfw,
            confidence: result.confidence || 0,
            details: result
        };
        
    } catch (error) {
        console.error('Error validando imagen:', error);
        // En caso de error, permitir imagen (ajusta según tu necesidad)
        return { isValid: true, confidence: 0, error: error.message };
    }
}

// ==========================================
// FUNCIONES DE UI
// ==========================================
export function showValidationIndicator() {
    document.getElementById('validationIndicator')?.classList.remove('hidden');
    document.getElementById('nsfwError')?.classList.add('hidden');
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.disabled = true;
}

export function hideValidationIndicator() {
    document.getElementById('validationIndicator')?.classList.add('hidden');
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.disabled = false;
}

export function showNSFWError() {
    document.getElementById('nsfwError')?.classList.remove('hidden');
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.disabled = true;
    isImageValid = false;
}

export function hideNSFWError() {
    document.getElementById('nsfwError')?.classList.add('hidden');
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.disabled = false;
    isImageValid = true;
}

export function getImageValidState() {
    return isImageValid;
}

export function setImageValidState(state) {
    isImageValid = state;
}