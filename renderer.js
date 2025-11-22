const canvas = document.getElementById('drawingCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight - 50;

const SCALE = 50; // 1 metro = 50 píxeles
let startPoint = null;
let lines = [];  // Lista para almacenar las líneas dibujadas
let selectedPoint = null;
let dragging = false;
const ANCHOR_THRESHOLD = 10; // Distancia mínima para considerar un punto como anclaje

// Manejar el clic en el botón de establecer punto de inicio
document.getElementById('setStartPointBtn').addEventListener('click', () => {
    canvas.addEventListener('click', setStartPoint, { once: true });
});

function setStartPoint(event) {
    const rect = canvas.getBoundingClientRect();
    startPoint = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
    };

    // Dibujar un punto visual en el canvas para marcar el punto de inicio
    drawPoint(startPoint.x, startPoint.y, "red");
}

// Función para dibujar una línea
function drawLine(length) {
    if (startPoint === null) {
        alert('Por favor, establece un punto de inicio antes de dibujar.');
        return;
    }

    const scaledLength = length * SCALE;
    const endX = startPoint.x + scaledLength;
    const endY = startPoint.y;

    lines.push({ startX: startPoint.x, startY: startPoint.y, endX, endY, length });

    // Redibuja el canvas con todas las líneas
    redrawCanvas();

    startPoint = { x: endX, y: endY };
}

// Función para dibujar un punto en el canvas
function drawPoint(x, y, color = "blue") {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fill();
}

// Función para eliminar todas las líneas
document.getElementById('deleteLineBtn').addEventListener('click', clearCanvas);

function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    startPoint = null;
    lines = [];
}

// Función para detectar si el clic está sobre un punto
function detectPointClick(event) {
    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    lines.forEach((line, index) => {
        if (isWithinPoint(clickX, clickY, line.startX, line.startY)) {
            selectedPoint = { type: 'start', lineIndex: index };
            dragging = true;
        } else if (isWithinPoint(clickX, clickY, line.endX, line.endY)) {
            selectedPoint = { type: 'end', lineIndex: index };
            dragging = true;
        }
    });
}

function isWithinPoint(clickX, clickY, pointX, pointY) {
    return (
        clickX >= pointX - ANCHOR_THRESHOLD &&
        clickX <= pointX + ANCHOR_THRESHOLD &&
        clickY >= pointY - ANCHOR_THRESHOLD &&
        clickY <= pointY + ANCHOR_THRESHOLD
    );
}

// Función para mover el punto seleccionado y ajustar las líneas conectadas
function movePoint(event) {
    if (dragging && selectedPoint !== null) {
        const rect = canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        const line = lines[selectedPoint.lineIndex];

        if (selectedPoint.type === 'end') {
            // Mantener el punto inicial como bisagra
            const angle = Math.atan2(mouseY - line.startY, mouseX - line.startX);

            // Calcular nuevas coordenadas del punto final manteniendo la longitud
            line.endX = mouseX;
            line.endY = mouseY;
            line.length = Math.sqrt((line.endX - line.startX) ** 2 + (line.endY - line.startY) ** 2) / SCALE;

            // Verificar si el punto final está cerca de otro punto para anclaje
            checkForAnchor(line.endX, line.endY, line, 'end');

            // Ajustar la línea siguiente si existe
            if (selectedPoint.lineIndex < lines.length - 1) {
                const nextLine = lines[selectedPoint.lineIndex + 1];
                nextLine.startX = line.endX;
                nextLine.startY = line.endY;
            }
        } else if (selectedPoint.type === 'start') {
            // Mantener el punto final como bisagra
            const angle = Math.atan2(line.endY - mouseY, line.endX - mouseX);

            // Calcular nuevas coordenadas del punto inicial manteniendo la longitud
            line.startX = mouseX;
            line.startY = mouseY;
            line.length = Math.sqrt((line.endX - line.startX) ** 2 + (line.endY - line.startY) ** 2) / SCALE;

            // Verificar si el punto inicial está cerca de otro punto para anclaje
            checkForAnchor(line.startX, line.startY, line, 'start');

            // Ajustar la línea anterior si existe
            if (selectedPoint.lineIndex > 0) {
                const prevLine = lines[selectedPoint.lineIndex - 1];
                prevLine.endX = line.startX;
                prevLine.endY = line.startY;
            }
        }

        // Redibuja el canvas con el punto movido y la etiqueta actualizada
        redrawCanvas();
    }
}

// Función para verificar si un punto debe anclarse a otro punto existente
function checkForAnchor(x, y, line, pointType) {
    lines.forEach(otherLine => {
        if (otherLine !== line) {
            if (isWithinPoint(x, y, otherLine.startX, otherLine.startY)) {
                if (pointType === 'start') {
                    line.startX = otherLine.startX;
                    line.startY = otherLine.startY;
                } else if (pointType === 'end') {
                    line.endX = otherLine.startX;
                    line.endY = otherLine.startY;
                }
            }
            if (isWithinPoint(x, y, otherLine.endX, otherLine.endY)) {
                if (pointType === 'start') {
                    line.startX = otherLine.endX;
                    line.startY = otherLine.endY;
                } else if (pointType === 'end') {
                    line.endX = otherLine.endX;
                    line.endY = otherLine.endY;
                }
            }
        }
    });
}

// Redibuja todas las líneas y puntos en el canvas
function redrawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    lines.forEach(line => {
        ctx.beginPath();
        ctx.moveTo(line.startX, line.startY);
        ctx.lineTo(line.endX, line.endY);
        ctx.stroke();

        drawPoint(line.startX, line.startY);
        drawPoint(line.endX, line.endY);

        const midX = (line.startX + line.endX) / 2;
        const midY = (line.startY + line.endY) / 2;
        ctx.font = "12px Arial";
        ctx.fillStyle = "black";
        ctx.fillText(`${line.length.toFixed(2)} m`, midX, midY - 10);
    });

    if (startPoint !== null && lines.length === 0) {
        drawPoint(startPoint.x, startPoint.y, "red");
    }
}

canvas.addEventListener('mousedown', detectPointClick);
canvas.addEventListener('mousemove', movePoint);
canvas.addEventListener('mouseup', () => {
    dragging = false;
    selectedPoint = null;
});

document.getElementById('drawLineBtn').addEventListener('click', () => {
    const length = parseFloat(document.getElementById('lineLength').value);

    if (isNaN(length) || length <= 0) {
        alert('Por favor, ingresa una longitud válida en metros.');
        return;
    }

    drawLine(length);
});
document.getElementById('exportSvgBtn').addEventListener('click', exportToSvg);

function exportToSvg() {
    // Crear un string que contendrá el contenido SVG
    let svgContent = `<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="${canvas.width}" height="${canvas.height}">\n`;

    lines.forEach(line => {
        svgContent += `<line x1="${line.startX}" y1="${line.startY}" x2="${line.endX}" y2="${line.endY}" stroke="black" stroke-width="2"/>\n`;

        const midX = (line.startX + line.endX) / 2;
        const midY = (line.startY + line.endY) / 2;
        svgContent += `<text x="${midX}" y="${midY - 10}" font-size="12" fill="black">${line.length.toFixed(2)} m</text>\n`;
    });

    svgContent += `</svg>`;

    // Crear un blob con el contenido SVG
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    // Crear un enlace para descargar el archivo
    const link = document.createElement('a');
    link.href = url;
    link.download = 'drawing.svg';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Liberar la URL creada
    URL.revokeObjectURL(url);
}

const DxfWriter = require('dxf-writer');
const fs = require('fs');

document.getElementById('exportDwgBtn').addEventListener('click', exportToDxf);

function exportToDxf() {
    const dxf = new DxfWriter();

    // Añadir líneas al archivo DXF
    lines.forEach(line => {
        dxf.addLine(line.startX, line.startY, line.endX, line.endY);
        const midX = (line.startX + line.endX) / 2;
        const midY = (line.startY + line.endY) / 2;
        dxf.addText(`${line.length.toFixed(2)} m`, midX, midY - 10, 12);
    });

    // Guardar el archivo DXF
    const dxfContent = dxf.toDxfString();
    fs.writeFileSync('drawing.dxf', dxfContent);
    alert('El archivo DXF ha sido exportado.');
}
