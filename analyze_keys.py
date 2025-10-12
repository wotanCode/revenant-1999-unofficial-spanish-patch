#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from collections import Counter, defaultdict

# Configurar stdout para UTF-8 en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_keys_with_positions(filename):
    """Extrae todas las keys con su posición de línea"""
    keys = []
    key_positions = defaultdict(list)
    
    # Intentar diferentes codificaciones
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    lines = None
    
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
    
    if lines is None:
        raise Exception(f"No se pudo leer el archivo {filename} con ninguna codificación")
        
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Ignorar comentarios y líneas vacías
        if not line or line.startswith('//'):
            i += 1
            continue
        
        # Buscar patrón KEY "valor"
        match = re.match(r'^(\w+)\s+"', line)
        if match:
            key = match.group(1)
            keys.append(key)
            key_positions[key].append(i + 1)  # línea número (1-indexed)
        
        i += 1
    
    return keys, key_positions

def analyze_files(original_file, translated_file):
    print("=" * 80)
    print("ANÁLISIS DE DIFERENCIAS ENTRE ARCHIVOS")
    print("=" * 80)
    
    # Extraer keys
    original_keys, original_positions = extract_keys_with_positions(original_file)
    translated_keys, translated_positions = extract_keys_with_positions(translated_file)
    
    # Contar keys
    original_counter = Counter(original_keys)
    translated_counter = Counter(translated_keys)
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"  - Archivo original: {len(original_keys)} keys totales ({len(set(original_keys))} únicas)")
    print(f"  - Archivo traducido: {len(translated_keys)} keys totales ({len(set(translated_keys))} únicas)")
    print(f"  - Diferencia: {len(original_keys) - len(translated_keys)} keys")
    
    # Keys que faltan en la traducción
    original_set = set(original_keys)
    translated_set = set(translated_keys)
    missing_keys = original_set - translated_set
    
    if missing_keys:
        print(f"\n❌ KEYS QUE FALTAN EN LA TRADUCCIÓN ({len(missing_keys)}):")
        for key in sorted(missing_keys):
            count = original_counter[key]
            positions = original_positions[key]
            if count > 1:
                print(f"  - {key} (aparece {count} veces en original, líneas: {positions})")
            else:
                print(f"  - {key} (línea {positions[0]} en original)")
    else:
        print(f"\n✅ No hay keys faltantes en la traducción")
    
    # Keys extra en la traducción
    extra_keys = translated_set - original_set
    
    if extra_keys:
        print(f"\n⚠️  KEYS EXTRA EN LA TRADUCCIÓN ({len(extra_keys)}):")
        for key in sorted(extra_keys):
            count = translated_counter[key]
            positions = translated_positions[key]
            if count > 1:
                print(f"  - {key} (aparece {count} veces, líneas: {positions})")
            else:
                print(f"  - {key} (línea {positions[0]})")
    else:
        print(f"\n✅ No hay keys extra en la traducción")
    
    # Keys duplicadas
    original_duplicates = {k: v for k, v in original_counter.items() if v > 1}
    translated_duplicates = {k: v for k, v in translated_counter.items() if v > 1}
    
    if original_duplicates:
        print(f"\n🔄 KEYS DUPLICADAS EN ORIGINAL ({len(original_duplicates)}):")
        for key, count in sorted(original_duplicates.items()):
            positions = original_positions[key]
            print(f"  - {key}: {count} veces (líneas: {positions})")
    
    if translated_duplicates:
        print(f"\n🔄 KEYS DUPLICADAS EN TRADUCCIÓN ({len(translated_duplicates)}):")
        for key, count in sorted(translated_duplicates.items()):
            positions = translated_positions[key]
            print(f"  - {key}: {count} veces (líneas: {positions})")
    
    # Verificar si las keys duplicadas se mantienen correctamente
    print(f"\n🔍 ANÁLISIS DE KEYS DUPLICADAS:")
    problematic_keys = []
    
    for key in original_duplicates:
        original_count = original_counter[key]
        translated_count = translated_counter.get(key, 0)
        
        if original_count != translated_count:
            problematic_keys.append(key)
            print(f"  ⚠️  {key}:")
            print(f"      Original: {original_count} veces (líneas: {original_positions[key]})")
            print(f"      Traducido: {translated_count} veces (líneas: {translated_positions.get(key, [])})")
    
    if not problematic_keys:
        print(f"  ✅ Todas las keys duplicadas se mantienen correctamente")
    
    # Verificar orden de keys (comparación posicional)
    print(f"\n🔢 VERIFICACIÓN DE ORDEN:")
    order_issues = []
    
    # Comparar solo las keys comunes
    common_keys = original_set & translated_set
    original_order = [k for k in original_keys if k in common_keys]
    translated_order = [k for k in translated_keys if k in common_keys]
    
    if original_order != translated_order:
        print(f"  ⚠️  El orden de las keys ha cambiado")
        # Mostrar primeras diferencias
        for i, (orig, trans) in enumerate(zip(original_order[:100], translated_order[:100])):
            if orig != trans:
                order_issues.append(i)
                if len(order_issues) <= 5:  # Mostrar solo las primeras 5
                    print(f"      Posición {i+1}: original='{orig}', traducido='{trans}'")
    else:
        print(f"  ✅ El orden de las keys se mantiene correcto")
    
    # Resumen final
    print(f"\n" + "=" * 80)
    print("RESUMEN:")
    print("=" * 80)
    
    issues_found = False
    
    if missing_keys:
        print(f"❌ {len(missing_keys)} keys faltantes en la traducción")
        issues_found = True
    
    if extra_keys:
        print(f"⚠️  {len(extra_keys)} keys extra en la traducción")
        issues_found = True
    
    if problematic_keys:
        print(f"⚠️  {len(problematic_keys)} keys duplicadas con conteo incorrecto")
        issues_found = True
    
    if order_issues:
        print(f"⚠️  El orden de las keys ha cambiado en {len(order_issues)} posiciones")
        issues_found = True
    
    if not issues_found:
        print(f"✅ No se encontraron diferencias estructurales")
    
    print("=" * 80)

if __name__ == "__main__":
    analyze_files("translations/english_original.def", "translations/english.def")
