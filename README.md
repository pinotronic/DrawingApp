# DrawingApp - Aplicación de Planos para Avalúos

Aplicación de dibujo técnico para crear planos de inmuebles destinada a empresas de avalúos. Permite dibujar el contorno de inmuebles con sus áreas de construcción y calcular medidas automáticamente.

## Características

- Dibujo de líneas con medidas precisas en metros
- Anclaje automático de puntos
- Modo de movimiento fijo (ángulos de 45°)
- Edición de medidas mediante doble clic
- Etiquetas personalizadas
- Exportación a formato SVG
- Cálculo automático de longitudes

## Requisitos

- Python 3.x
- tkinter (incluido en Python estándar)

## Uso

```bash
python main.py
```

## Funcionalidades

1. **Dibujar Línea**: Ingresa la longitud en metros y dibuja
2. **Establecer Punto de Inicio**: Define el punto inicial del dibujo
3. **Movimiento Fijo**: Restringe ángulos a múltiplos de 45°
4. **Agregar Etiquetas**: Añade texto personalizado al plano
5. **Exportar a SVG**: Guarda el plano en formato vectorial

## Estructura del Proyecto

```
DrawingApp/
├── main.py          # Aplicación principal (Tkinter)
├── index.html       # Interfaz web (Electron)
├── renderer.js      # Lógica del canvas web
├── main.js          # Proceso principal Electron
├── preload.js       # Script de precarga Electron
├── styles.css       # Estilos CSS
└── assets/          # Recursos adicionales
```

## Desarrollo

Desarrollado para empresas de avalúos inmobiliarios que requieren crear planos técnicos de forma rápida y precisa.

## Licencia

MIT
