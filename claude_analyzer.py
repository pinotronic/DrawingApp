"""
Módulo de integración con Claude AI (Anthropic) para análisis inteligente de planos.
Proporciona análisis geométrico avanzado y sugerencias para avalúos inmobiliarios.
"""

import os
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
from geometry_utils import GeometryUtils
from dotenv import load_dotenv


class ClaudeAnalyzer:
    """
    Analizador inteligente de planos usando Claude AI.
    Proporciona análisis geométrico, detección de inconsistencias y sugerencias.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el analizador con la API key de Claude.
        
        Args:
            api_key: API key de Anthropic. Si no se proporciona, se lee de variable de entorno.
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        
        if not self.api_key or self.api_key == 'tu_api_key_aqui':
            raise ValueError(
                "API key de Claude no configurada. "
                "Por favor, edita el archivo .env y configura CLAUDE_API_KEY con tu clave real."
            )
        
        self.client = Anthropic(api_key=self.api_key)
        # Usar Claude Sonnet 4.5 - versión más reciente disponible
        # Alias: claude-sonnet-4-5 (apunta automáticamente a la versión más nueva)
        # Versión específica: claude-sonnet-4-5-20250929
        self.model = "claude-sonnet-4-5"
        self.geo_utils = GeometryUtils()
    
    def analyze_floor_plan(self, lines: List[Dict], scale: float = 50, zones: List[Dict] = None) -> Dict:
        """
        Analiza un plano completo y genera un reporte detallado.
        
        Args:
            lines: Lista de líneas del plano con 'start', 'end' y 'length'
            scale: Escala de píxeles a metros
            zones: Lista opcional de zonas/habitaciones con sus áreas
        
        Returns:
            Diccionario con análisis completo y recomendaciones
        """
        # Realizar cálculos geométricos locales
        local_analysis = self._perform_local_analysis(lines, scale, zones)
        
        # Enviar a Claude para análisis inteligente
        claude_analysis = self._get_claude_analysis(local_analysis, zones)
        
        # Combinar resultados
        return {
            'measurements': local_analysis['measurements'],
            'geometry': local_analysis['geometry'],
            'issues': local_analysis['issues'],
            'zones': local_analysis.get('zones'),
            'claude_insights': claude_analysis,
            'timestamp': self._get_timestamp()
        }
    
    def _perform_local_analysis(self, lines: List[Dict], scale: float, zones: List[Dict] = None) -> Dict:
        """
        Realiza análisis geométrico local sin usar la API.
        
        Args:
            lines: Lista de líneas
            scale: Escala
            zones: Lista opcional de zonas
        
        Returns:
            Diccionario con resultados del análisis local
        """
        # Convertir coordenadas de píxeles a metros
        lines_in_meters = self._convert_to_meters(lines, scale)
        
        # Cálculos básicos
        area = self.geo_utils.calculate_polygon_area(lines_in_meters)
        perimeter = self.geo_utils.calculate_perimeter(lines)
        is_closed = self.geo_utils.detect_closed_polygon(lines_in_meters)
        regularity = self.geo_utils.calculate_shape_regularity(lines)
        
        # Detección de patrones
        parallel_lines = self.geo_utils.detect_parallel_lines(lines)
        perpendicular_lines = self.geo_utils.detect_perpendicular_lines(lines)
        irregular_angles = self.geo_utils.detect_irregular_angles(lines)
        
        # Sugerencias de corrección
        suggestions = self.geo_utils.suggest_corrections(lines, scale)
        
        # Procesar información de zonas si está disponible
        zones_info = None
        if zones:
            zones_info = self._process_zones_info(zones)
        
        result = {
            'measurements': {
                'area_m2': round(area, 2),
                'perimeter_m': round(perimeter, 2),
                'num_lines': len(lines),
                'is_closed': is_closed,
                'regularity_index': round(regularity, 2)
            },
            'geometry': {
                'parallel_pairs': len(parallel_lines),
                'perpendicular_pairs': len(perpendicular_lines),
                'irregular_angles_count': len(irregular_angles),
                'irregular_angles_details': irregular_angles
            },
            'issues': {
                'suggestions': suggestions,
                'has_issues': len(suggestions) > 0,
                'severity_counts': self._count_severities(suggestions)
            }
        }
        
        if zones_info:
            result['zones'] = zones_info
        
        return result
    
    def _get_claude_analysis(self, local_analysis: Dict, zones: List[Dict] = None) -> Dict:
        """
        Envía los datos a Claude para obtener análisis inteligente.
        
        Args:
            local_analysis: Resultados del análisis local
            zones: Lista opcional de zonas
        
        Returns:
            Respuesta procesada de Claude
        """
        prompt = self._build_analysis_prompt(local_analysis, zones)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Baja temperatura para respuestas más precisas
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = message.content[0].text
            
            return {
                'analysis': response_text,
                'success': True,
                'model_used': self.model
            }
            
        except Exception as e:
            return {
                'analysis': f"Error al conectar con Claude: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    def _build_analysis_prompt(self, local_analysis: Dict, zones: List[Dict] = None) -> str:
        """
        Construye el prompt para Claude basado en el análisis local.
        
        Args:
            local_analysis: Datos del análisis local
            zones: Lista opcional de zonas
        
        Returns:
            Prompt formateado para Claude
        """
        measurements = local_analysis['measurements']
        geometry = local_analysis['geometry']
        issues = local_analysis['issues']
        
        prompt = f"""Eres un experto en análisis de planos arquitectónicos y avalúos inmobiliarios.

Analiza el siguiente plano de un inmueble con base en sus características geométricas:

**MEDIDAS GENERALES:**
- Área total: {measurements['area_m2']} m²
- Perímetro: {measurements['perimeter_m']} m
- Número de líneas/muros: {measurements['num_lines']}
- Polígono cerrado: {'Sí' if measurements['is_closed'] else 'No'}
- Índice de regularidad: {measurements['regularity_index']} (0-1, donde 1 es muy regular)

**GEOMETRÍA:**
- Líneas paralelas detectadas: {geometry['parallel_pairs']} pares
- Líneas perpendiculares: {geometry['perpendicular_pairs']} pares
- Ángulos irregulares: {geometry['irregular_angles_count']}
"""

        # Agregar información de zonas si está disponible
        if zones and 'zones' in local_analysis:
            zones_data = local_analysis['zones']
            prompt += f"""
**DISTRIBUCIÓN POR ZONAS/HABITACIONES:**
- Total de zonas definidas: {zones_data['total_zones']}
- Zonas válidas (cerradas): {zones_data['valid_zones']}
- Área total de zonas: {zones_data['total_area']} m²

Desglose por tipo de zona:
"""
            for zone_type, info in zones_data['by_type'].items():
                prompt += f"  • {zone_type.capitalize()}: {info['count']} zona(s), {info['total_area']:.2f} m²\n"
            
            prompt += "\nZonas individuales:\n"
            for zone in zones_data['zones_list']:
                status = "✅" if zone['is_valid'] else "⚠️"
                prompt += f"  {status} {zone['name']} ({zone['type']}): {zone['area']:.2f} m²\n"

        prompt += f"""
**PROBLEMAS DETECTADOS:**
- Total de sugerencias: {len(issues['suggestions'])}
- Severidad alta: {issues['severity_counts'].get('high', 0)}
- Severidad media: {issues['severity_counts'].get('medium', 0)}

Proporciona un análisis estructurado en las siguientes secciones:

1. **RESUMEN EJECUTIVO**: Descripción general del inmueble (2-3 líneas)

2. **ANÁLISIS GEOMÉTRICO**: Evalúa la forma, regularidad y características del plano
"""
        
        if zones:
            prompt += """
3. **DISTRIBUCIÓN DE ESPACIOS**: Analiza la distribución de zonas/habitaciones:
   - Proporción de áreas por tipo de espacio
   - Funcionalidad de la distribución
   - Comparación con estándares de mercado
   - Recomendaciones sobre distribución

4. **INCONSISTENCIAS DETECTADAS**: Lista y explica los problemas encontrados

5. **IMPACTO EN AVALÚO**: Cómo estas características afectan el valor del inmueble

6. **RECOMENDACIONES**: Sugerencias específicas para corrección o documentación
"""
        else:
            prompt += """
3. **INCONSISTENCIAS DETECTADAS**: Lista y explica los problemas encontrados

4. **IMPACTO EN AVALÚO**: Cómo estas características afectan el valor del inmueble

5. **RECOMENDACIONES**: Sugerencias específicas para corrección o documentación
"""

        prompt += "\nSé específico, profesional y enfocado en avalúos inmobiliarios."
        
        return prompt
    
    def _process_zones_info(self, zones: List[Dict]) -> Dict:
        """
        Procesa la información de zonas para el análisis.
        
        Args:
            zones: Lista de diccionarios con información de zonas
        
        Returns:
            Diccionario con estadísticas de zonas procesadas
        """
        total_zones = len(zones)
        valid_zones = sum(1 for z in zones if z.get('is_valid', False))
        total_area = sum(z.get('area', 0) for z in zones if z.get('is_valid', False))
        
        # Agrupar por tipo
        by_type = {}
        for zone in zones:
            zone_type = zone.get('type', 'otro')
            if zone_type not in by_type:
                by_type[zone_type] = {
                    'count': 0,
                    'total_area': 0.0,
                    'zones': []
                }
            
            by_type[zone_type]['count'] += 1
            by_type[zone_type]['total_area'] += zone.get('area', 0)
            by_type[zone_type]['zones'].append(zone.get('name', 'Sin nombre'))
        
        return {
            'total_zones': total_zones,
            'valid_zones': valid_zones,
            'invalid_zones': total_zones - valid_zones,
            'total_area': round(total_area, 2),
            'by_type': by_type,
            'zones_list': zones
        }
    
    # Métodos auxiliares
    
    def _convert_to_meters(self, lines: List[Dict], scale: float) -> List[Dict]:
        """Convierte coordenadas de píxeles a metros."""
        converted = []
        for line in lines:
            converted.append({
                'start': (line['start'][0] / scale, line['start'][1] / scale),
                'end': (line['end'][0] / scale, line['end'][1] / scale),
                'length': line.get('length', 0)
            })
        return converted
    
    def _count_severities(self, suggestions: List[Dict]) -> Dict[str, int]:
        """Cuenta sugerencias por nivel de severidad."""
        counts = {'high': 0, 'medium': 0, 'low': 0}
        for suggestion in suggestions:
            severity = suggestion.get('severity', 'low')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def format_report(self, analysis: Dict) -> str:
        """
        Formatea el análisis en un reporte legible.
        
        Args:
            analysis: Diccionario con el análisis completo
        
        Returns:
            Reporte formateado como string
        """
        measurements = analysis['measurements']
        geometry = analysis['geometry']
        issues = analysis['issues']
        claude = analysis['claude_insights']
        zones = analysis.get('zones')
        
        report = f"""
═══════════════════════════════════════════════════════════════
            REPORTE DE ANÁLISIS DE PLANO - AVALÚO
═══════════════════════════════════════════════════════════════

Fecha de análisis: {analysis['timestamp']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📐 MEDICIONES PRINCIPALES

  • Área total:        {measurements['area_m2']} m²
  • Perímetro:         {measurements['perimeter_m']} m
  • Número de muros:   {measurements['num_lines']}
  • Polígono cerrado:  {'✓ Sí' if measurements['is_closed'] else '✗ No'}
  • Regularidad:       {measurements['regularity_index']} / 1.00
"""

        # Agregar sección de zonas si están disponibles
        if zones:
            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 DISTRIBUCIÓN POR ZONAS/HABITACIONES

  • Total de zonas:    {zones['total_zones']}
  • Zonas válidas:     {zones['valid_zones']}
  • Área de zonas:     {zones['total_area']} m²

  Desglose por tipo:
"""
            for zone_type, info in zones['by_type'].items():
                report += f"    {zone_type.capitalize():15} {info['count']} zona(s)  |  {info['total_area']:.2f} m²\n"
            
            report += "\n  Detalle de zonas:\n"
            for zone in zones['zones_list']:
                status = "✅" if zone['is_valid'] else "⚠️"
                report += f"    {status} {zone['name']:20} ({zone['type']:10}) {zone['area']:7.2f} m²\n"

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 ANÁLISIS GEOMÉTRICO

  • Líneas paralelas:       {geometry['parallel_pairs']} pares
  • Líneas perpendiculares: {geometry['perpendicular_pairs']} pares
  • Ángulos irregulares:    {geometry['irregular_angles_count']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  PROBLEMAS DETECTADOS

  Total de sugerencias: {len(issues['suggestions'])}
  
  Severidad:
    🔴 Alta:   {issues['severity_counts'].get('high', 0)}
    🟡 Media:  {issues['severity_counts'].get('medium', 0)}
    🟢 Baja:   {issues['severity_counts'].get('low', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 ANÁLISIS INTELIGENTE CON IA (Claude)

{claude['analysis'] if claude['success'] else '❌ ' + claude['analysis']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Modelo: {claude.get('model_used', 'N/A')}

═══════════════════════════════════════════════════════════════
"""
        return report


# Función auxiliar para cargar variables de entorno desde .env
def load_env_file(filepath: str = '.env'):
    """
    Carga variables de entorno desde un archivo .env usando python-dotenv.
    
    Args:
        filepath: Ruta al archivo .env
    """
    load_dotenv(filepath)
