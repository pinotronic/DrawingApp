# DrawingApp - Aplicación de Planos para Avalúos con IA

Aplicación de dibujo técnico para crear planos de inmuebles destinada a empresas de avalúos. Permite dibujar el contorno de inmuebles con sus áreas de construcción, calcular medidas automáticamente y **analizar planos con Inteligencia Artificial** usando Claude de Anthropic.

## ✨ Características

### Dibujo Técnico
- Dibujo de líneas con medidas precisas en metros
- Anclaje automático de puntos
- Modo de movimiento fijo (ángulos de 45°)
- Edición de medidas mediante doble clic
- Etiquetas personalizadas
- Exportación a formato SVG
- Cálculo automático de longitudes

### 🤖 Análisis con IA (Claude)
- **Cálculo automático de áreas** totales y perímetros
- **Identificación de inconsistencias** en medidas y geometría
- **Detección de ángulos irregulares** y líneas no paralelas/perpendiculares
- **Sugerencias inteligentes** para correcciones
- **Análisis de impacto en avalúo** basado en características del inmueble
- **Reportes profesionales** listos para documentación

## 📋 Requisitos

- Python 3.10 o superior
- tkinter (incluido en Python estándar)
- anthropic (SDK de Claude)
- python-dotenv

## 🚀 Instalación

1. **Clona el repositorio:**
```bash
git clone https://github.com/pinotronic/DrawingApp.git
cd DrawingApp
```

2. **Crea un entorno virtual (recomendado):**
```bash
python -m venv .venv
```

3. **Activa el entorno virtual:**
   - Windows (PowerShell):
     ```bash
     .venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```bash
     .venv\Scripts\activate.bat
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Instala las dependencias:**
```bash
pip install -r requirements.txt
```

5. **Configura tu API Key de Claude:**
   - Abre el archivo `.env`
   - Reemplaza `tu_api_key_aqui` con tu API key real de Anthropic
   - Puedes obtener tu API key en: https://console.anthropic.com/

```env
CLAUDE_API_KEY=tu_clave_aqui
```

## 💻 Uso

```bash
python main.py
```

### Funcionalidades Principales

1. **Dibujar Línea**: Ingresa la longitud en metros y dibuja
2. **Establecer Punto de Inicio**: Define el punto inicial del dibujo
3. **Movimiento Fijo**: Restringe ángulos a múltiplos de 45°
4. **Agregar Etiquetas**: Añade texto personalizado al plano
5. **Exportar a SVG**: Guarda el plano en formato vectorial
6. **🤖 Análisis IA**: Analiza el plano con inteligencia artificial

### Ejemplo de Análisis con IA

1. Dibuja el contorno de un inmueble con varias líneas
2. Haz clic en el botón **"🤖 Análisis IA"**
3. Espera unos segundos mientras Claude analiza
4. Revisa el reporte completo con:
   - Mediciones (área, perímetro)
   - Análisis geométrico
   - Problemas detectados
   - Recomendaciones profesionales
5. Copia o guarda el reporte para documentación

## 📁 Estructura del Proyecto

```
DrawingApp/
├── main.py                  # Aplicación principal (Tkinter)
├── claude_analyzer.py       # Módulo de análisis con Claude AI
├── geometry_utils.py        # Utilidades para cálculos geométricos
├── requirements.txt         # Dependencias de Python
├── .env                     # Configuración de API keys (no subir a git)
├── .gitignore              # Archivos excluidos de git
├── README.md               # Este archivo
├── index.html              # Interfaz web (Electron) - alternativa
├── renderer.js             # Lógica del canvas web
├── main.js                 # Proceso principal Electron
├── preload.js              # Script de precarga Electron
├── styles.css              # Estilos CSS
└── assets/                 # Recursos adicionales
```

## 🔒 Seguridad

- **IMPORTANTE**: Nunca compartas tu API key de Claude públicamente
- El archivo `.env` está en `.gitignore` para proteger tus credenciales
- Las API keys son personales y no deben subirse al repositorio

## 🤝 Contribución

Este proyecto es de código abierto. Si deseas contribuir:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📝 Desarrollo

Desarrollado para empresas de avalúos inmobiliarios que requieren crear planos técnicos de forma rápida y precisa, con análisis inteligente asistido por IA.

## 🧠 Tecnologías

- **Python 3.14** - Lenguaje principal
- **Tkinter** - Interfaz gráfica
- **Claude AI (Anthropic)** - Análisis inteligente de planos
- **SVG** - Exportación de gráficos vectoriales

## 📄 Licencia

MIT

---

**¿Necesitas ayuda?** Abre un issue en GitHub o consulta la documentación de Claude en https://docs.anthropic.com/
