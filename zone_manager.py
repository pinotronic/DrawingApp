"""
Gestor de zonas para planos de inmuebles.
Permite crear, editar y gestionar zonas/habitaciones en el plano.
"""

from typing import List, Dict, Tuple, Optional
import random
from geometry_utils import GeometryUtils


class Zone:
    """Representa una zona o habitación en el plano."""
    
    def __init__(self, zone_id: int, name: str, zone_type: str, 
                 line_indices: List[int], color: str = None):
        """
        Inicializa una zona.
        
        Args:
            zone_id: ID único de la zona
            name: Nombre de la zona (ej: "Sala", "Cocina")
            zone_type: Tipo de zona (ej: "habitacion", "bano", "cocina")
            line_indices: Índices de las líneas que forman esta zona
            color: Color en formato hex para visualización
        """
        self.id = zone_id
        self.name = name
        self.zone_type = zone_type
        self.line_indices = line_indices
        self.color = color or self._generate_pastel_color()
        self.area = 0.0  # Se calcula después
        self.is_valid = False  # Se valida después
    
    def _generate_pastel_color(self) -> str:
        """Genera un color pastel aleatorio para la zona."""
        r = random.randint(180, 255)
        g = random.randint(180, 255)
        b = random.randint(180, 255)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def to_dict(self) -> Dict:
        """Convierte la zona a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.zone_type,
            'line_indices': self.line_indices,
            'color': self.color,
            'area': self.area,
            'is_valid': self.is_valid
        }


class ZoneManager:
    """Gestor de zonas para el plano."""
    
    # Tipos de zonas predefinidos
    ZONE_TYPES = {
        'sala': {'icon': '🛋️', 'color': '#FFE4B5'},
        'cocina': {'icon': '🍳', 'color': '#FFB6C1'},
        'comedor': {'icon': '🍽️', 'color': '#DDA0DD'},
        'recamara': {'icon': '🛏️', 'color': '#B0E0E6'},
        'bano': {'icon': '🚿', 'color': '#87CEEB'},
        'estudio': {'icon': '📚', 'color': '#98FB98'},
        'jardin': {'icon': '🌳', 'color': '#90EE90'},
        'garage': {'icon': '🚗', 'color': '#D3D3D3'},
        'pasillo': {'icon': '🚪', 'color': '#F5DEB3'},
        'terraza': {'icon': '☀️', 'color': '#FFDAB9'},
        'bodega': {'icon': '📦', 'color': '#C0C0C0'},
        'lavanderia': {'icon': '🧺', 'color': '#E0FFFF'},
        'otro': {'icon': '📐', 'color': '#F0F0F0'}
    }
    
    def __init__(self, scale: float = 50):
        """
        Inicializa el gestor de zonas.
        
        Args:
            scale: Escala de píxeles a metros
        """
        self.zones: List[Zone] = []
        self.scale = scale
        self.next_id = 1
        self.geo_utils = GeometryUtils()
    
    def create_zone(self, name: str, zone_type: str, line_indices: List[int], 
                    all_lines: List[Dict]) -> Optional[Zone]:
        """
        Crea una nueva zona.
        
        Args:
            name: Nombre de la zona
            zone_type: Tipo de zona
            line_indices: Índices de las líneas que forman la zona
            all_lines: Lista completa de líneas del plano
        
        Returns:
            Zona creada o None si hay error
        """
        if not line_indices:
            return None
        
        # Obtener las líneas de la zona
        zone_lines = [all_lines[i] for i in line_indices if i < len(all_lines)]
        
        if len(zone_lines) < 3:
            return None
        
        # Crear la zona
        color = self.ZONE_TYPES.get(zone_type, {}).get('color')
        zone = Zone(self.next_id, name, zone_type, line_indices, color)
        self.next_id += 1
        
        # Validar y calcular área
        zone.is_valid = self.geo_utils.validate_zone_closure(zone_lines, tolerance=20.0)
        
        if zone.is_valid:
            zone.area = self.geo_utils.calculate_zone_area(zone_lines, self.scale)
        
        self.zones.append(zone)
        return zone
    
    def delete_zone(self, zone_id: int) -> bool:
        """
        Elimina una zona por su ID.
        
        Args:
            zone_id: ID de la zona a eliminar
        
        Returns:
            True si se eliminó exitosamente
        """
        for i, zone in enumerate(self.zones):
            if zone.id == zone_id:
                del self.zones[i]
                return True
        return False
    
    def update_zone(self, zone_id: int, name: str = None, zone_type: str = None,
                   line_indices: List[int] = None, all_lines: List[Dict] = None) -> bool:
        """
        Actualiza una zona existente.
        
        Args:
            zone_id: ID de la zona a actualizar
            name: Nuevo nombre (opcional)
            zone_type: Nuevo tipo (opcional)
            line_indices: Nuevos índices de líneas (opcional)
            all_lines: Lista completa de líneas (requerido si se actualizan índices)
        
        Returns:
            True si se actualizó exitosamente
        """
        zone = self.get_zone(zone_id)
        if not zone:
            return False
        
        if name:
            zone.name = name
        
        if zone_type:
            zone.zone_type = zone_type
            zone.color = self.ZONE_TYPES.get(zone_type, {}).get('color') or zone.color
        
        if line_indices and all_lines:
            zone.line_indices = line_indices
            zone_lines = [all_lines[i] for i in line_indices if i < len(all_lines)]
            zone.is_valid = self.geo_utils.validate_zone_closure(zone_lines, tolerance=20.0)
            if zone.is_valid:
                zone.area = self.geo_utils.calculate_zone_area(zone_lines, self.scale)
        
        return True
    
    def get_zone(self, zone_id: int) -> Optional[Zone]:
        """Obtiene una zona por su ID."""
        for zone in self.zones:
            if zone.id == zone_id:
                return zone
        return None
    
    def get_zone_by_line(self, line_index: int) -> Optional[Zone]:
        """Obtiene la zona que contiene una línea específica."""
        for zone in self.zones:
            if line_index in zone.line_indices:
                return zone
        return None
    
    def get_all_zones(self) -> List[Zone]:
        """Retorna todas las zonas."""
        return self.zones.copy()
    
    def get_zones_summary(self) -> Dict:
        """
        Genera un resumen de todas las zonas.
        
        Returns:
            Diccionario con estadísticas de las zonas
        """
        total_area = sum(z.area for z in self.zones if z.is_valid)
        zone_count = len(self.zones)
        valid_zones = sum(1 for z in self.zones if z.is_valid)
        
        zones_by_type = {}
        for zone in self.zones:
            if zone.zone_type not in zones_by_type:
                zones_by_type[zone.zone_type] = {
                    'count': 0,
                    'total_area': 0.0,
                    'zones': []
                }
            zones_by_type[zone.zone_type]['count'] += 1
            zones_by_type[zone.zone_type]['total_area'] += zone.area
            zones_by_type[zone.zone_type]['zones'].append(zone.name)
        
        return {
            'total_zones': zone_count,
            'valid_zones': valid_zones,
            'invalid_zones': zone_count - valid_zones,
            'total_area': round(total_area, 2),
            'zones_by_type': zones_by_type,
            'zones_list': [z.to_dict() for z in self.zones]
        }
    
    def get_zone_centroid(self, zone_id: int, all_lines: List[Dict]) -> Optional[Tuple[float, float]]:
        """
        Obtiene el centroide de una zona para colocar la etiqueta.
        
        Args:
            zone_id: ID de la zona
            all_lines: Lista completa de líneas
        
        Returns:
            Tupla (x, y) con el centroide o None
        """
        zone = self.get_zone(zone_id)
        if not zone:
            return None
        
        zone_lines = [all_lines[i] for i in zone.line_indices if i < len(all_lines)]
        if not zone_lines:
            return None
        
        return self.geo_utils.get_zone_centroid(zone_lines)
    
    def auto_detect_zones(self, all_lines: List[Dict]) -> List[Zone]:
        """
        Intenta detectar automáticamente zonas cerradas en el plano.
        
        Args:
            all_lines: Lista completa de líneas del plano
        
        Returns:
            Lista de zonas detectadas automáticamente
        """
        detected_zones = []
        used_lines = set()
        
        for i, line in enumerate(all_lines):
            if i in used_lines:
                continue
            
            # Buscar líneas conectadas
            connected = self.geo_utils.find_connected_lines(all_lines, i, tolerance=10.0)
            
            if len(connected) >= 3:
                zone_lines = [all_lines[idx] for idx in connected]
                
                # Verificar si forma un polígono cerrado
                if self.geo_utils.validate_zone_closure(zone_lines, tolerance=10.0):
                    # Crear zona auto-detectada
                    zone_name = f"Zona {len(detected_zones) + 1}"
                    zone = self.create_zone(zone_name, 'otro', connected, all_lines)
                    
                    if zone:
                        detected_zones.append(zone)
                        used_lines.update(connected)
        
        return detected_zones
    
    def clear_all_zones(self):
        """Elimina todas las zonas."""
        self.zones.clear()
        self.next_id = 1
    
    def get_zone_label(self, zone: Zone) -> str:
        """
        Genera la etiqueta de texto para mostrar en la zona.
        
        Args:
            zone: Zona
        
        Returns:
            Texto de la etiqueta
        """
        icon = self.ZONE_TYPES.get(zone.zone_type, {}).get('icon', '📐')
        return f"{icon} {zone.name}\n{zone.area:.2f} m²"
    
    def export_zones_data(self) -> List[Dict]:
        """Exporta la información de todas las zonas."""
        return [zone.to_dict() for zone in self.zones]
    
    def import_zones_data(self, zones_data: List[Dict], all_lines: List[Dict]):
        """
        Importa zonas desde datos guardados.
        
        Args:
            zones_data: Lista de diccionarios con datos de zonas
            all_lines: Lista completa de líneas del plano
        """
        self.clear_all_zones()
        
        for data in zones_data:
            zone = Zone(
                data['id'],
                data['name'],
                data['type'],
                data['line_indices'],
                data.get('color')
            )
            zone.area = data.get('area', 0.0)
            zone.is_valid = data.get('is_valid', False)
            
            self.zones.append(zone)
            self.next_id = max(self.next_id, zone.id + 1)
