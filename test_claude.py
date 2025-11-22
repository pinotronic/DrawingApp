"""
Script de prueba para verificar la integración de Claude AI.
Ejecuta un análisis simulado sin necesidad de la interfaz gráfica.
"""

from claude_analyzer import ClaudeAnalyzer, load_env_file
from geometry_utils import GeometryUtils
import os

def test_claude_integration():
    """Prueba básica de la integración con Claude."""
    
    print("=" * 70)
    print("PRUEBA DE INTEGRACIÓN CON CLAUDE AI")
    print("=" * 70)
    print()
    
    # Cargar variables de entorno
    print("1. Cargando configuración...")
    load_env_file('.env')
    
    # Verificar API key
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key or api_key == 'tu_api_key_aqui':
        print("❌ ERROR: API key no configurada")
        print()
        print("Por favor, edita el archivo .env y configura tu API key:")
        print("   CLAUDE_API_KEY=tu_clave_real_aqui")
        print()
        return False
    
    print(f"✓ API key encontrada: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # Crear plano de ejemplo (un rectángulo simple)
    print("2. Creando plano de ejemplo (rectángulo de 10m x 8m)...")
    scale = 50  # 1 metro = 50 píxeles
    
    # Rectángulo: punto inicial (50, 50)
    lines = [
        {'start': (50, 50), 'end': (550, 50), 'length': 10.0},      # Línea superior
        {'start': (550, 50), 'end': (550, 450), 'length': 8.0},     # Línea derecha
        {'start': (550, 450), 'end': (50, 450), 'length': 10.0},    # Línea inferior
        {'start': (50, 450), 'end': (50, 50), 'length': 8.0}        # Línea izquierda
    ]
    
    print(f"✓ Plano creado con {len(lines)} líneas")
    print()
    
    # Inicializar analizador
    print("3. Inicializando Claude Analyzer...")
    try:
        analyzer = ClaudeAnalyzer()
        print("✓ Analizador inicializado correctamente")
        print()
    except Exception as e:
        print(f"❌ ERROR al inicializar: {e}")
        return False
    
    # Realizar análisis
    print("4. Analizando plano con Claude AI...")
    print("   (Esto puede tardar unos segundos...)")
    print()
    
    try:
        analysis = analyzer.analyze_floor_plan(lines, scale)
        
        # Mostrar resultados
        print("✓ Análisis completado con éxito!")
        print()
        print("=" * 70)
        print("RESULTADOS DEL ANÁLISIS")
        print("=" * 70)
        print()
        
        # Mediciones
        measurements = analysis['measurements']
        print("📐 MEDICIONES:")
        print(f"   • Área: {measurements['area_m2']} m²")
        print(f"   • Perímetro: {measurements['perimeter_m']} m")
        print(f"   • Polígono cerrado: {'Sí' if measurements['is_closed'] else 'No'}")
        print(f"   • Índice de regularidad: {measurements['regularity_index']}")
        print()
        
        # Análisis de Claude
        claude = analysis['claude_insights']
        if claude['success']:
            print("🤖 ANÁLISIS DE CLAUDE:")
            print("-" * 70)
            print(claude['analysis'])
            print("-" * 70)
        else:
            print(f"❌ Error en análisis de Claude: {claude.get('error', 'Desconocido')}")
        
        print()
        print("=" * 70)
        print("✓ PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR durante el análisis: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_claude_integration()
