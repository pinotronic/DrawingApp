"""
Utilidades para cálculos geométricos en planos de inmuebles.
Proporciona funciones para análisis de áreas, perímetros y validaciones.
"""

import math
from typing import List, Tuple, Dict, Optional


class GeometryUtils:
    """Clase con métodos estáticos para cálculos geométricos."""
    
    @staticmethod
    def calculate_polygon_area(lines: List[Dict]) -> float:
        """
        Calcula el área de un polígono cerrado usando el método del trapecio (Shoelace formula).
        
        Args:
            lines: Lista de diccionarios con 'start' y 'end' como tuplas (x, y)
        
        Returns:
            Área en metros cuadrados
        """
        if len(lines) < 3:
            return 0.0
        
        # Extraer todos los vértices únicos en orden
        vertices = GeometryUtils._extract_vertices(lines)
        
        if len(vertices) < 3:
            return 0.0
        
        # Aplicar fórmula del trapecio
        area = 0.0
        n = len(vertices)
        for i in range(n):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % n]
            area += (x1 * y2 - x2 * y1)
        
        return abs(area) / 2.0
    
    @staticmethod
    def calculate_perimeter(lines: List[Dict]) -> float:
        """
        Calcula el perímetro total sumando las longitudes de todas las líneas.
        
        Args:
            lines: Lista de diccionarios con información de líneas
        
        Returns:
            Perímetro en metros
        """
        return sum(line.get('length', 0) for line in lines)
    
    @staticmethod
    def detect_closed_polygon(lines: List[Dict], tolerance: float = 0.1) -> bool:
        """
        Detecta si las líneas forman un polígono cerrado.
        
        Args:
            lines: Lista de líneas
            tolerance: Tolerancia en metros para considerar puntos iguales
        
        Returns:
            True si el polígono está cerrado
        """
        if len(lines) < 3:
            return False
        
        vertices = GeometryUtils._extract_vertices(lines)
        
        # Verificar si el primer y último vértice son el mismo (o muy cercanos)
        first = vertices[0]
        last = vertices[-1]
        distance = math.sqrt((first[0] - last[0])**2 + (first[1] - last[1])**2)
        
        return distance <= tolerance
    
    @staticmethod
    def detect_parallel_lines(lines: List[Dict], angle_tolerance: float = 5.0) -> List[Tuple[int, int]]:
        """
        Detecta pares de líneas paralelas.
        
        Args:
            lines: Lista de líneas
            angle_tolerance: Tolerancia en grados para considerar líneas paralelas
        
        Returns:
            Lista de tuplas (índice1, índice2) de líneas paralelas
        """
        parallel_pairs = []
        n = len(lines)
        
        for i in range(n):
            for j in range(i + 1, n):
                angle1 = GeometryUtils._get_line_angle(lines[i])
                angle2 = GeometryUtils._get_line_angle(lines[j])
                
                # Normalizar ángulos a [0, 180)
                angle1 = angle1 % 180
                angle2 = angle2 % 180
                
                angle_diff = abs(angle1 - angle2)
                
                # Considerar tanto 0° como 180° (líneas en direcciones opuestas pero paralelas)
                if angle_diff <= angle_tolerance or angle_diff >= (180 - angle_tolerance):
                    parallel_pairs.append((i, j))
        
        return parallel_pairs
    
    @staticmethod
    def detect_perpendicular_lines(lines: List[Dict], angle_tolerance: float = 5.0) -> List[Tuple[int, int]]:
        """
        Detecta pares de líneas perpendiculares (ángulo de 90°).
        
        Args:
            lines: Lista de líneas
            angle_tolerance: Tolerancia en grados
        
        Returns:
            Lista de tuplas (índice1, índice2) de líneas perpendiculares
        """
        perpendicular_pairs = []
        n = len(lines)
        
        for i in range(n):
            for j in range(i + 1, n):
                angle1 = GeometryUtils._get_line_angle(lines[i])
                angle2 = GeometryUtils._get_line_angle(lines[j])
                
                angle_diff = abs(angle1 - angle2) % 180
                
                # Verificar si están cerca de 90°
                if abs(angle_diff - 90) <= angle_tolerance:
                    perpendicular_pairs.append((i, j))
        
        return perpendicular_pairs
    
    @staticmethod
    def detect_irregular_angles(lines: List[Dict], expected_angles: List[float] = [0, 45, 90, 135, 180], 
                               tolerance: float = 5.0) -> List[Dict]:
        """
        Detecta líneas con ángulos irregulares que no se ajustan a los esperados.
        
        Args:
            lines: Lista de líneas
            expected_angles: Ángulos esperados en grados
            tolerance: Tolerancia en grados
        
        Returns:
            Lista de diccionarios con información de líneas irregulares
        """
        irregular = []
        
        for i, line in enumerate(lines):
            angle = GeometryUtils._get_line_angle(line) % 180
            
            # Verificar si el ángulo está cerca de alguno esperado
            is_regular = any(abs(angle - exp) <= tolerance or abs(angle - (exp + 180)) <= tolerance 
                           for exp in expected_angles)
            
            if not is_regular:
                irregular.append({
                    'index': i,
                    'angle': angle,
                    'closest_expected': min(expected_angles, key=lambda x: abs(angle - x))
                })
        
        return irregular
    
    @staticmethod
    def calculate_shape_regularity(lines: List[Dict]) -> float:
        """
        Calcula un índice de regularidad del polígono (0-1, donde 1 es muy regular).
        
        Args:
            lines: Lista de líneas
        
        Returns:
            Índice de regularidad entre 0 y 1
        """
        if len(lines) < 3:
            return 0.0
        
        # Calcular desviación estándar de longitudes
        lengths = [line.get('length', 0) for line in lines]
        mean_length = sum(lengths) / len(lengths)
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        
        # Normalizar (invertir para que mayor regularidad = valor más alto)
        if mean_length > 0:
            length_regularity = 1 - min(std_dev / mean_length, 1)
        else:
            length_regularity = 0
        
        # Calcular regularidad de ángulos
        angles = [GeometryUtils._get_line_angle(line) % 180 for line in lines]
        angle_variance = sum((a - 90) ** 2 for a in angles) / len(angles)
        angle_regularity = 1 - min(angle_variance / 8100, 1)  # 90^2 = 8100
        
        # Promedio ponderado
        return (length_regularity * 0.6 + angle_regularity * 0.4)
    
    @staticmethod
    def suggest_corrections(lines: List[Dict], scale: float = 50) -> List[Dict]:
        """
        Sugiere correcciones para líneas irregulares.
        
        Args:
            lines: Lista de líneas
            scale: Escala de píxeles a metros
        
        Returns:
            Lista de sugerencias de corrección
        """
        suggestions = []
        
        # Detectar ángulos irregulares
        irregular_angles = GeometryUtils.detect_irregular_angles(lines)
        
        for item in irregular_angles:
            idx = item['index']
            current_angle = item['angle']
            closest = item['closest_expected']
            
            suggestions.append({
                'type': 'angle_correction',
                'line_index': idx,
                'current_angle': round(current_angle, 2),
                'suggested_angle': closest,
                'severity': 'medium' if abs(current_angle - closest) < 10 else 'high'
            })
        
        # Detectar longitudes inconsistentes
        lengths = [line.get('length', 0) for line in lines]
        if lengths:
            mean_length = sum(lengths) / len(lengths)
            
            for i, length in enumerate(lengths):
                deviation = abs(length - mean_length) / mean_length if mean_length > 0 else 0
                
                if deviation > 0.5:  # Más de 50% de desviación
                    suggestions.append({
                        'type': 'length_inconsistency',
                        'line_index': i,
                        'current_length': round(length, 2),
                        'average_length': round(mean_length, 2),
                        'severity': 'high' if deviation > 1.0 else 'medium'
                    })
        
        return suggestions
    
    # Métodos auxiliares privados
    
    @staticmethod
    def _extract_vertices(lines: List[Dict]) -> List[Tuple[float, float]]:
        """Extrae vértices únicos de las líneas en orden."""
        if not lines:
            return []
        
        vertices = [lines[0]['start']]
        
        for line in lines:
            if vertices[-1] != line['start']:
                vertices.append(line['start'])
            vertices.append(line['end'])
        
        # Remover duplicados consecutivos
        unique_vertices = [vertices[0]]
        for v in vertices[1:]:
            if v != unique_vertices[-1]:
                unique_vertices.append(v)
        
        return unique_vertices
    
    @staticmethod
    def _get_line_angle(line: Dict) -> float:
        """Calcula el ángulo de una línea en grados."""
        start = line['start']
        end = line['end']
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        return math.degrees(math.atan2(dy, dx))
    
    @staticmethod
    def format_area(area: float) -> str:
        """Formatea el área con la unidad apropiada."""
        return f"{area:.2f} m²"
    
    @staticmethod
    def format_length(length: float) -> str:
        """Formatea la longitud con la unidad apropiada."""
        return f"{length:.2f} m"
    
    @staticmethod
    def calculate_zone_area(zone_lines: List[Dict], scale: float = 50) -> float:
        """
        Calcula el área de una zona específica definida por un conjunto de líneas.
        
        Args:
            zone_lines: Lista de líneas que definen la zona
            scale: Escala de píxeles a metros
        
        Returns:
            Área de la zona en metros cuadrados
        """
        if not zone_lines or len(zone_lines) < 3:
            return 0.0
        
        # Convertir coordenadas a metros
        lines_in_meters = []
        for line in zone_lines:
            lines_in_meters.append({
                'start': (line['start'][0] / scale, line['start'][1] / scale),
                'end': (line['end'][0] / scale, line['end'][1] / scale),
                'length': line.get('length', 0)
            })
        
        return GeometryUtils.calculate_polygon_area(lines_in_meters)
    
    @staticmethod
    def get_zone_centroid(zone_lines: List[Dict]) -> Tuple[float, float]:
        """
        Calcula el centroide (punto central) de una zona para colocar la etiqueta.
        
        Args:
            zone_lines: Lista de líneas que definen la zona
        
        Returns:
            Tupla (x, y) con las coordenadas del centroide
        """
        if not zone_lines:
            return (0, 0)
        
        vertices = GeometryUtils._extract_vertices(zone_lines)
        
        if not vertices:
            return (0, 0)
        
        # Calcular centroide simple (promedio de vértices)
        x_sum = sum(v[0] for v in vertices)
        y_sum = sum(v[1] for v in vertices)
        n = len(vertices)
        
        return (x_sum / n, y_sum / n)
    
    @staticmethod
    def validate_zone_closure(zone_lines: List[Dict], tolerance: float = 10.0) -> bool:
        """
        Valida que las líneas de una zona formen un polígono cerrado.
        
        Args:
            zone_lines: Lista de líneas de la zona
            tolerance: Tolerancia en píxeles para considerar el polígono cerrado
        
        Returns:
            True si la zona está cerrada correctamente
        """
        if len(zone_lines) < 3:
            return False
        
        vertices = GeometryUtils._extract_vertices(zone_lines)
        
        if len(vertices) < 3:
            return False
        
        # Verificar si el primer y último vértice están cerca
        first = vertices[0]
        last = vertices[-1]
        distance = math.sqrt((first[0] - last[0])**2 + (first[1] - last[1])**2)
        
        return distance <= tolerance
    
    @staticmethod
    def find_connected_lines(all_lines: List[Dict], start_line_index: int, 
                            tolerance: float = 10.0) -> List[int]:
        """
        Encuentra todas las líneas conectadas a partir de una línea inicial.
        Útil para auto-detectar zonas.
        
        Args:
            all_lines: Lista completa de líneas del plano
            start_line_index: Índice de la línea inicial
            tolerance: Distancia máxima para considerar puntos conectados
        
        Returns:
            Lista de índices de líneas conectadas
        """
        if start_line_index >= len(all_lines):
            return []
        
        connected = {start_line_index}
        to_check = [start_line_index]
        
        while to_check:
            current_idx = to_check.pop()
            current_line = all_lines[current_idx]
            
            # Buscar líneas conectadas
            for i, line in enumerate(all_lines):
                if i in connected:
                    continue
                
                # Verificar si comparten algún punto
                if (GeometryUtils._points_near(current_line['start'], line['start'], tolerance) or
                    GeometryUtils._points_near(current_line['start'], line['end'], tolerance) or
                    GeometryUtils._points_near(current_line['end'], line['start'], tolerance) or
                    GeometryUtils._points_near(current_line['end'], line['end'], tolerance)):
                    
                    connected.add(i)
                    to_check.append(i)
        
        return list(connected)
    
    @staticmethod
    def _points_near(p1: Tuple[float, float], p2: Tuple[float, float], 
                     tolerance: float) -> bool:
        """Verifica si dos puntos están cerca según la tolerancia."""
        distance = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        return distance <= tolerance
