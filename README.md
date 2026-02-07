## Estructura del Proyecto Django (Backend)

# 📝 Reporte de mejoras: Validación de Nombre de Usuario y Comentarios
**Fecha:** 2025-08-18  
**Autor:** [Eduardo Alberto Sanchez Lebron]  

---

## 🔐 1. Validación de nombre de usuario (`UsernameValidator`)

Se creó una clase centralizada para validar nombres de usuario con las siguientes reglas:

- ✅ Longitud mínima: `2`, recomendada: `4`
- ✅ Longitud máxima: `15`
- ❌ Rechazo de nombres compuestos **solo por números**
- ❌ Rechazo de palabras prohibidas (`admin`, insultos, etc.)
- ❌ Rechazo de duplicados en la base de datos (`username__iexact`)
- ✅ Mensajes personalizados por error

Se separó la lógica de verificación en base de datos mediante:

```python```
is_username_taken(username, exclude_user_id=id)

---

# 📝 Reporte de mejoras: Dark modo 
**Fecha:** 2025-08-19  
**Autor:** [Eduardo Alberto Sanchez Lebron]  
### 🎨 1. Temas dinámicos en la aplicación

Se implementó un sistema de **temas dinámicos** para toda la aplicación, permitiendo que los usuarios puedan cambiar entre:

- **Default** (claro)  
- **Dark** (oscuro)  
- **Blue** (azul)  en trabajo
- **Sunset** (atardecer)  en trabajo
- **Forest** (bosque)  en trabajo

**Cambios realizados:**  
✅ Variables CSS centralizadas (`--color-primary`, `--color-text`, etc.)  
✅ Persistencia del tema usando `localStorage`  
✅ Transiciones suaves en colores y sombras para una experiencia más fluida  
✅ Botones y dropdowns adaptados a los distintos temas  

> Inicialmente pensé que sería complicado implementar temas con Tailwind, pero la potencia de sus **variables CSS** y **clases utilitarias** hizo que fuera más fácil de lo que imaginaba.


