#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vuln_lookup_cvss_fixed.py

VERSIONE CORRETTA FINALE con:
- Calcolo CVSS accurato da tutte le fonti (NVD, CIRCL, OSV)
- Filtraggio per versione specifica quando disponibile
- CVSS calcolato SOLO sui CVE specifici per la versione target
- FIX ENCODING WINDOWS per emoji
- FIX estrazione descrizioni CVE 5.0 da CIRCL
- OUTPUT UNIFORME per tutte le fonti
"""

import argparse
import csv
import json
import requests
import time
import sys
import os
import re
from datetime import datetime

HEADERS = {"User-Agent": "vuln-lookup-real/1.0"}

# -------------------------
# Filtraggio versione
# -------------------------
def compare_versions(v1: str, v2: str) -> int:
    """
    Confronta versioni. Ritorna: -1 (v1<v2), 0 (uguali), 1 (v1>v2)
    Gestisce anche alpha/beta/rc: 2.0-beta < 2.0
    """
    try:
        # Pulisci versioni
        v1_clean = v1.lower().replace('v', '').strip()
        v2_clean = v2.lower().replace('v', '').strip()
        
        # Separa numero da suffisso (alpha/beta/rc)
        def parse_version(v):
            # Match: "2.0-beta7" → groups: ("2.0", "beta", "7")
            match = re.match(r'^(\d+(?:\.\d+)*)(?:[-_]?(alpha|beta|rc|m|milestone|preview|snapshot)(\d*))?', v)
            if not match:
                return ([0], None, 0)
            
            # Estrai parti numeriche
            num_str = match.group(1)
            nums = [int(x) for x in num_str.split('.')]
            
            # Estrai suffisso e numero suffisso
            suffix = match.group(2)  # alpha/beta/rc/etc
            suffix_num = int(match.group(3)) if match.group(3) else 0
            
            return (nums, suffix, suffix_num)
        
        v1_nums, v1_suffix, v1_suffix_num = parse_version(v1_clean)
        v2_nums, v2_suffix, v2_suffix_num = parse_version(v2_clean)
        
        # Normalizza lunghezza
        max_len = max(len(v1_nums), len(v2_nums))
        v1_nums.extend([0] * (max_len - len(v1_nums)))
        v2_nums.extend([0] * (max_len - len(v2_nums)))
        
        # Confronta numeri principali
        for i in range(max_len):
            if v1_nums[i] < v2_nums[i]:
                return -1
            elif v1_nums[i] > v2_nums[i]:
                return 1
        
        # Numeri uguali → confronta suffissi
        # Regola: 2.0-beta < 2.0 (versione con suffisso è MINORE)
        suffix_priority = {
            'alpha': 1,
            'beta': 2,
            'rc': 3,
            'm': 4,
            'milestone': 4,
            'preview': 5,
            'snapshot': 6,
            None: 999  # Versione finale = priorità massima
        }
        
        v1_priority = suffix_priority.get(v1_suffix, 0)
        v2_priority = suffix_priority.get(v2_suffix, 0)
        
        if v1_priority < v2_priority:
            return -1
        elif v1_priority > v2_priority:
            return 1
        else:
            # Stesso suffisso, confronta numero suffisso
            if v1_suffix_num < v2_suffix_num:
                return -1
            elif v1_suffix_num > v2_suffix_num:
                return 1
        
        return 0
    except Exception as e:
        # In caso di errore, considera uguali
        return 0

def matches_version_prefix(target_version: str, prefix_pattern: str) -> bool:
    """
    Verifica se target matcha un pattern di prefisso tipo "2.x", "1.2.x"
    Esempi:
    - matches_version_prefix("2.14.1", "2.x") → True
    - matches_version_prefix("3.0.0", "2.x") → False
    - matches_version_prefix("1.2.17", "1.2.x") → True
    """
    if not prefix_pattern or not target_version:
        return False
    
    # Rimuovi ".x" o ".*" dalla fine
    prefix = prefix_pattern.lower().replace('.x', '').replace('.*', '').strip()
    
    if not prefix:
        return True
    
    target_lower = target_version.lower().strip()
    
    # Se prefix è solo un numero (es. "2"), target deve iniziare con "2."
    if '.' not in prefix:
        return target_lower.startswith(f"{prefix}.")
    
    # Altrimenti: target deve iniziare con prefix + "."
    return target_lower.startswith(f"{prefix}.")

def parse_version_ranges(description: str, product: str) -> list:
    """
    Estrae range di versioni vulnerabili dalla descrizione CVE.
    APPROCCIO MIGLIORATO: estrazione in due fasi
    """
    product_lower = re.escape(product.lower())
    
    # Pattern versione SENZA gruppi di cattura esterni (per evitare confusione)
    version_regex = r"\d+(?:\.\d+)*(?:[-_]?(?:alpha|beta|rc|m|milestone|preview|snapshot)\d*)?"
    
    ranges = []
    exclusions = []
    desc_lower = description.lower() if description else ""

    # ========================================
    # FASE 0: PATTERN CON WILDCARD "X.x"
    # ========================================
    # Gestisce: "Product 2.x before 2.8.2", "version 1.x"
    
    # Pattern: "Product X.x before Y.Z"
    wildcard_before = rf"{product_lower}\s+(\d+(?:\.\d+)?\.x)\s+before\s+({version_regex})"
    for match in re.finditer(wildcard_before, desc_lower):
        ranges.append(("prefix_range", match.group(1), match.group(2)))
    
    # Pattern: "version X.x before Y.Z" (senza nome prodotto)
    wildcard_before_generic = rf"versions?\s+(\d+(?:\.\d+)?\.x)\s+(?:before|prior\s+to)\s+({version_regex})"
    for match in re.finditer(wildcard_before_generic, desc_lower):
        ranges.append(("prefix_range", match.group(1), match.group(2)))
    
    # ========================================
    # FASE 1: ESCLUSIONI ESPLICITE
    # ========================================
    excluding_match = re.search(
        rf"\(excluding(?:\s+security\s+fix\s+releases?)?\s+([^\)]+)\)", 
        desc_lower
    )
    if excluding_match:
        excl_text = excluding_match.group(1)
        excl_versions = re.findall(version_regex, excl_text)
        exclusions.extend(excl_versions)
        
    # ========================================
    # FASE 2: "FIXED IN" - Pattern più specifici
    # ========================================
    
    # Approccio semplificato: cerca "fixed in" seguito da testo che contiene versioni
    # Cattura tutto tra "fixed in" e il prossimo punto/fine riga
    fixed_in_pattern = rf"fixed\s+in\s+([^\.]+)"
    for match in re.finditer(fixed_in_pattern, desc_lower):
        text_after_fixed = match.group(1)
        
        # Verifica che menzioni il prodotto (opzionale ma utile)
        # Estrai TUTTE le versioni valide dal testo catturato
        found_versions = re.findall(version_regex, text_after_fixed)
        
        if found_versions:
            for ver in found_versions:
                # Salta versioni palesemente sbagliate come "1" o "2" (troppo corte)
                if '.' in ver:
                    ranges.append(("range", None, ver))
# ========================================
# FASE 3: "VERSION X.Y (details) AND VERSION A.B (details) FIX"
# ========================================
# Pattern: "Log4j 2.16.0 (Java 8) and 2.12.2 (Java 7) fix this issue"
    version_fix_pattern1 = rf"{product_lower}\s+({version_regex}\s*\([^)]+\)(?:\s+and\s+{version_regex}\s*\([^)]+\))+)\s+(?:fix|patch|address)"

    for match in re.finditer(version_fix_pattern1, desc_lower):
        fix_text = match.group(1)
        fix_versions = re.findall(version_regex, fix_text)
        for ver in fix_versions:
            ranges.append(("range", None, ver))

    # Pattern senza nome prodotto
   
    version_fix_pattern2 = rf"({version_regex}\s*\([^)]+\)(?:\s+and\s+{version_regex}\s*\([^)]+\))+)\s+(?:fix|patch|address)"
    for match in re.finditer(version_fix_pattern2, desc_lower):
        fix_text = match.group(1)
        fix_versions = re.findall(version_regex, fix_text)
        for ver in fix_versions:
            ranges.append(("range", None, ver))
    
    # ========================================
    # FASE 4: RANGE ESPLICITI "X through Y"
    # ========================================
    range_patterns = [
        (rf"{product_lower}.*?versions?\s+({version_regex})\s+through\s+({version_regex})", "range"),
        (rf"({version_regex})\s+through\s+({version_regex})", "range"),
        (rf"from\s+({version_regex})\s+to\s+({version_regex})", "range"),
        (rf"between\s+({version_regex})\s+and\s+({version_regex})", "range"),
    ]
    
    for pattern, kind in range_patterns:
        for match in re.finditer(pattern, desc_lower):
            if len(match.groups()) == 2:
                ranges.append(("range", match.group(1), match.group(2)))
    
    # ========================================
    # FASE 5: RANGE APERTI "before X", "after X"
    # ========================================
    open_range_patterns = [
        (rf"before\s+({version_regex})", "before"),
        (rf"prior\s+to\s+({version_regex})", "before"),
        (rf"up\s+to\s+(?:and\s+including\s+)?({version_regex})", "upto"),
        (rf"after\s+({version_regex})", "after"),
        (rf"since\s+({version_regex})", "after"),
    ]
    
    for pattern, kind in open_range_patterns:
        for match in re.finditer(pattern, desc_lower):
            if kind in ["before", "upto"]:
                ranges.append(("range", None, match.group(1)))
            else:  # after/since
                ranges.append(("range", match.group(1), None))
    
    # ========================================
    # AGGIUNGI ESCLUSIONI COME TIPO SPECIALE
    # ========================================
    for excl_version in exclusions:
        ranges.append(("exclude", excl_version))
    
    return ranges

def is_version_vulnerable(target_version: str, cve_description: str, product: str, debug=False) -> bool:
    """Determina se la versione è vulnerabile - VERSIONE PIÙ RESTRITTIVA"""
    
    if not target_version:
        if debug:
            print(f"      DEBUG: No target version - include by default")
        return True
    
    if not cve_description or cve_description.strip() == "":
        if debug:
            print(f"      DEBUG: Empty description - EXCLUDE (strict mode)")
        return False
    
    description_lower = cve_description.lower()
    target_v = target_version.lower().strip()
    product_lower = product.lower()
    
    # ✅ FIX 1: Verifica che il CVE menzioni il prodotto
    if product_lower not in description_lower:
        if debug:
            print(f"      DEBUG: Product '{product}' not mentioned - EXCLUDE")
        return False
    
    # ✅ FIX 2: Esclude CVE che menzionano altri prodotti simili
    excluded_patterns = [
        r'\bother\s+versions?\b',
        r'\bexcept\b',
        r'\bonly\s+affects?\b'
    ]
    
    for pattern in excluded_patterns:
        if re.search(pattern, description_lower):
            if debug:
                print(f"      DEBUG: Exclusion pattern '{pattern}' found - needs manual review")
    
    # Menzione esplicita della versione target
    version_patterns = [
        f" {target_v}",
        f"v{target_v}",
        f"_{target_v}",
        f"version {target_v}",
        f"release {target_v}"
    ]
    
    for pattern in version_patterns:
        if pattern in description_lower:
            if debug:
                print(f"      DEBUG: Version {target_v} explicitly mentioned - INCLUDE")
            return True
    
    # "all versions" - controlla che non parli di prefix diverso (es. "all versions of 1.x" quando target è 2.x)
    if "all version" in description_lower or "any version" in description_lower:
        # Cerca pattern "X.x" menzionati
        mentioned_prefixes = re.findall(r'\b(\d+(?:\.\d+)?\.x)\b', description_lower)
        
        if mentioned_prefixes:
            # Controlla se target matcha ALMENO UN prefisso
            matches_any = any(matches_version_prefix(target_v, prefix) for prefix in mentioned_prefixes)
            if not matches_any:
                if debug:
                    print(f"      DEBUG: 'all versions' but refers to {mentioned_prefixes[0]}, target is {target_v} - EXCLUDE")
                return False
        
        if debug:
            print(f"      DEBUG: 'all versions' keyword - INCLUDE")
        return True
    
    # Range di versioni
    ranges = parse_version_ranges(cve_description, product)
    
    if not ranges:
        # ✅ FIX 3: Più restrittivo - se non ci sono range E non c'è menzione esplicita, ESCLUDI
        generic_keywords = ["unspecified", "unknown version"]
        if any(kw in description_lower for kw in generic_keywords):
            if debug:
                print(f"      DEBUG: Generic keyword but no range - EXCLUDE (too vague)")
            return False
        
        if debug:
            print(f"      DEBUG: No version info found - EXCLUDE")
        return False
    
    # ✅ STEP 1: Controlla se la versione è esplicitamente ESCLUSA
    exclusions = [r[1] for r in ranges if r[0] == "exclude"]
    for excl_version in exclusions:
        if compare_versions(target_v, excl_version) == 0:
            if debug:
                print(f"      DEBUG: Version {target_v} explicitly EXCLUDED - EXCLUDE")
            return False

    # ✅ STEP 2: Controlla se rientra nei range vulnerabili
    vulnerability_ranges = [r for r in ranges if r[0] != "exclude"]

    for r in vulnerability_ranges:
        kind = r[0]
        
        # Gestione range con wildcard (es. "2.x before 2.8.2")
        if kind == "prefix_range":
            prefix_pattern = r[1]  # es. "2.x"
            end_version = r[2]      # es. "2.8.2"
            
            if matches_version_prefix(target_v, prefix_pattern):
                if compare_versions(target_v, end_version) < 0:
                    if debug:
                        print(f"      DEBUG: Matches prefix {prefix_pattern} and < {end_version} - INCLUDE")
                    return True
                else:
                    if debug:
                        print(f"      DEBUG: Matches prefix {prefix_pattern} but >= {end_version} - EXCLUDE")
            continue
        if kind == "single":
            version = r[1]
            if compare_versions(target_v, version) == 0:
                if debug:
                    print(f"      DEBUG: Exact match {target_v} == {version} - INCLUDE")
                return True
        elif kind == "range":
            start, end = r[1], r[2]
            start_ok = True if start is None else compare_versions(target_v, start) >= 0
            end_ok = True if end is None else compare_versions(target_v, end) < 0  # ✅ CAMBIATO: < invece di <=
            if start_ok and end_ok:
                if debug:
                    print(f"      DEBUG: In range [{start or '-inf'}, {end or 'inf'}] - INCLUDE")
                return True

    if debug:
        print(f"      DEBUG: Not in any range - EXCLUDE")
    return False

def save_circl_descriptions(results, fname="circl_descriptions.json"):
    """
    Salva TUTTE le descrizioni di CIRCL (NON filtrate) in formato JSON come lista:
    [
      "product version: description",
      "product version: description",
      ...
    ]
    """
    descriptions_list = []
    
    for result in results:
        product = result.get('product', 'unknown')
        version = result.get('version', '')
        
        # Crea il prefisso "product version"
        prefix = f"{product} {version}".strip() if version else product
        
        # Estrai i risultati NON FILTRATI da CIRCL
        circl_data = result.get('full', {}).get('circl_unfiltered', [])
        
        for block in circl_data:
            for hit in block.get('hits', []):
                description = hit.get('summary', '') or hit.get('description', '')
                
                if description:
                    # Formato: "product version: description"
                    full_description = f"{prefix}: {description}"
                    descriptions_list.append(full_description)
    
    # Salva in JSON
    if descriptions_list:
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(descriptions_list, f, ensure_ascii=False, indent=2)
        
        print(f"Descrizioni CIRCL salvate: {fname}")
        print(f"   {len(descriptions_list)} descrizioni totali (NON filtrate)")
        return True
    else:
        print("Nessuna descrizione CIRCL da salvare")
        return False

def filter_results_by_version(results: list, target_version: str, product: str, debug=False) -> dict:
    """Filtra CVE per versione specifica"""
    if not target_version:
        return {
            "filtered_results": results,
            "total_before": len(results),
            "total_after": len(results),
            "filtered_out": 0
        }
    
    filtered = []
    if debug:
        print(f"\n   === DEBUG FILTER for version {target_version} ===")
    
    for result in results:
        cve_id = result.get('id') or result.get('cve', 'UNKNOWN')
        description = result.get('summary', '') or result.get('description', '')
        
        if debug:
            print(f"\n   Checking {cve_id}:")
            print(f"      Description: {description}..." if description else "      No description")
        
        if is_version_vulnerable(target_version, description, product, debug=debug):
            filtered.append(result)
    
    if debug:
        print(f"\n   === END DEBUG ===\n")
    
    return {
        "filtered_results": filtered,
        "total_before": len(results),
        "total_after": len(filtered),
        "filtered_out": len(results) - len(filtered)
    }

# -------------------------
# Estrazione CVSS 
# -------------------------
def extract_cvss_from_cve(cve_data: dict) -> float:
    """Estrae CVSS da qualsiasi struttura CVE (NVD, CIRCL, OSV)"""
    
    if cve_data.get('cvss') is not None:
        try:
            return float(cve_data['cvss'])
        except:
            pass
    
    if 'metrics' in cve_data:
        metrics = cve_data['metrics']
        try:
            # Cerca source "nvd@nist.gov" o "Primary" come priorità 
            for metric_type in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if metrics.get(metric_type):
                    for metric in metrics[metric_type]:
                        if metric.get("type") == "Primary" or metric.get("source") == "nvd@nist.gov":
                            return float(metric["cvssData"]["baseScore"])
                    # Se non c'è Primary, prendi il primo disponibile
                    return float(metrics[metric_type][0]["cvssData"]["baseScore"])
        except:
            pass
    
    # Campo cvss diretto
    if cve_data.get('cvss') is not None:
        try:
            return float(cve_data['cvss'])
        except:
            pass
    # Supporto CVE 5.0 - metrics dentro containers.cna
    if 'containers' in cve_data:
        try:
            containers = cve_data['containers']
            if 'cna' in containers:
                cna = containers['cna']
                if 'metrics' in cna:
                    metrics_list = cna['metrics']
                    if isinstance(metrics_list, list) and len(metrics_list) > 0:
                        for metric in metrics_list:
                            if 'other' in metric:
                                continue
                            if 'cvssV3_1' in metric:
                                return float(metric['cvssV3_1'].get('baseScore', 0))
                            elif 'cvssV3_0' in metric:
                                return float(metric['cvssV3_0'].get('baseScore', 0))
                            elif 'cvssV2_0' in metric:
                                return float(metric['cvssV2_0'].get('baseScore', 0))
            if 'adp' in containers:
                adp_array = containers['adp']
                if isinstance(adp_array, list):
                    for adp_item in adp_array:
                        if isinstance(adp_item, dict) and 'metrics' in adp_item:
                            metrics_list = adp_item['metrics']
                            if isinstance(metrics_list, list):
                                for metric in metrics_list:
                                    if 'cvssV3_1' in metric:
                                        return float(metric['cvssV3_1'].get('baseScore', 0))
                                    elif 'cvssV3_0' in metric:
                                        return float(metric['cvssV3_0'].get('baseScore', 0))
                                    elif 'cvssV2_0' in metric:
                                        return float(metric['cvssV2_0'].get('baseScore', 0))

        except:
            pass
    
    if 'cvss' in cve_data:
        try:
            cvss_val = cve_data['cvss']
            if isinstance(cvss_val, (int, float)):
                return float(cvss_val)
            elif isinstance(cvss_val, dict):
                return float(cvss_val.get('score') or cvss_val.get('baseScore', 0))
        except:
            pass
    
    if 'impact' in cve_data:
        try:
            impact = cve_data['impact']
            if isinstance(impact, dict):
                for version in ['baseMetricV3', 'baseMetricV2']:
                    if version in impact:
                        return float(impact[version].get('cvssV3', {}).get('baseScore') or 
                                   impact[version].get('cvssV2', {}).get('baseScore', 0))
        except:
            pass
    
    return None

# -------------------------
# Query NVD
# -------------------------
def query_nvd_cpe(vendor: str, product: str, version: str, debug=False) -> list:
    """Query NVD con CPE esatto"""
    try:
        time.sleep(1)
        vendor_clean = vendor.replace(" ", "_").replace("-", "_")
        version_clean = version.replace(" ", "_").replace("+", "_")
        
        cpe_type = "o" if any(kw in product.lower() for kw in 
                             ["windows", "linux", "freertos", "android", "vxworks"]) else "a"
        
        cpe = f"cpe:2.3:{cpe_type}:{vendor_clean}:{product}:{version_clean}:*:*:*:*:*:*:*"
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        r = requests.get(url, headers=HEADERS, params={"cpeName": cpe}, timeout=15)
        r.raise_for_status()
        
        results = []
        for item in r.json().get("vulnerabilities", []):
            cve = item.get("cve", {})
            
            desc = ""
            try:
                desc = cve.get("descriptions", [{}])[0].get("value", "")
            except:
                pass
            
            cvss = extract_cvss_from_cve(cve)
            cve_id = cve.get("id")
            
            # OUTPUT UNIFORME
            if debug and cve_id:
                cvss_str = f"CVSS:{cvss:.1f}" if cvss else "NO CVSS"
                print(f"   [NVD] {cve_id} - {cvss_str}")
                if desc:
                    print(f"         {desc[:100]}...")
            
            results.append({
                "id": cve_id, 
                "summary": desc, 
                "cvss": cvss,
                "raw": item
            })
        
        return results
    except Exception as e:
        if debug:
            print(f"   [NVD] ERRORE: {e}")
        return []

def query_nvd_keyword(keyword: str, debug=False) -> list:
    """Query NVD con keyword"""
    try:
        time.sleep(2)
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        r = requests.get(url, headers=HEADERS, params={"keywordSearch": keyword}, timeout=20)
        r.raise_for_status()
        
        results = []
        for item in r.json().get("vulnerabilities", []):
            cve = item.get("cve", {})
            
            desc = ""
            try:
                desc = cve.get("descriptions", [{}])[0].get("value", "")
            except:
                pass
            
            cvss = extract_cvss_from_cve(cve)
            cve_id = cve.get("id")
            
            # OUTPUT UNIFORME
            if debug and cve_id:
                cvss_str = f"CVSS:{cvss:.1f}" if cvss else "NO CVSS"
                print(f"   [NVD] {cve_id} - {cvss_str}")
                if desc:
                    print(f"         {desc[:100]}...")
            
            results.append({
                "id": cve_id, 
                "summary": desc, 
                "cvss": cvss,
                "raw": item
            })
        
        return results
    except Exception as e:
        if debug:
            print(f"   [NVD] ERRORE: {e}")
        return []

def smart_nvd_search(product: str, vendor=None, version=None, debug=False) -> list:
    """Ricerca NVD con priorità CPE (se versione presente) e fallback keyword"""
    
    if debug:
        print(f"\n   >>> INTERROGAZIONE NVD")

    # 1️ Caso: abbiamo anche la versione → prova prima CPE
    if version:
        results = query_nvd_cpe(vendor, product, version, debug=debug)
        if results:
            print(f"   [NVD] {len(results)} risultati CPE per {vendor or 'unknown'}:{product}:{version}")
            return results
        
        if debug:
            print(f"   [NVD] Nessun risultato CPE, fallback su keyword")

        # fallback → ricerca keyword con filtro versione
        keyword = f"{product} {version}"
        results = query_nvd_keyword(keyword, debug=debug)

        if results:
            filtered = filter_results_by_version(results, version, product, debug=debug)
            if filtered["filtered_out"] > 0:
                print(f"   [NVD] Filtro versione: {filtered['total_before']} -> {filtered['total_after']} specifici per v{version}")
            return filtered["filtered_results"]

        return []

    # 2️ Caso: non abbiamo versione → solo keyword generica
    results = query_nvd_keyword(product, debug=debug)
    return results or []



# -------------------------
# Query CIRCL
# -------------------------
def query_circl(vendor, product, version=None, debug=True) -> list:
    """Query CIRCL con estrazione CVSS e descrizioni migliorata - OUTPUT UNIFORME"""
    try:
        if not vendor:
            return []
        
        if debug:
            print(f"\n   >>> INTERROGAZIONE CIRCL")
        #circl accetta solo get

        url = f"https://cve.circl.lu/api/vulnerability/search/{vendor}/{product}"

        r = requests.get(url, headers=HEADERS, timeout=15)

        # Controlla lo status e stampa i primi elementi
        if r.status_code == 200:
            data = r.json()
        else:
            print(f"Errore HTTP: {r.status_code}")
        r.raise_for_status()
        
        with open("cve_results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        #Se c'è 'results', usa quello come dizionario principale
        if 'results' in data:
            data = data['results']
    
        results = []
       
        
        # Itera su tutte le fonti presenti nel JSON
        for source, items in data.items():
            # print(f"Source: {source}, Type: {type(items)}, Items: {len(items) if isinstance(items, list) else 'N/A'}")
            #salta chiavi che non sono liste
            if not isinstance(items, list):
                continue
            
            for item in items:
                try:
                    cve_data = None
                    cve_id = None
                    
                    # Estrai CVE ID e dati in base alla struttura
                    if isinstance(item, dict):
                        cve_data = item
                        cve_id = item.get("id")
                    elif isinstance(item, list) and len(item) >= 2:
                        cve_id = item[0]
                        cve_data = item[1]
                    
                    if not cve_data or not cve_id:
                        continue
                    clean_cve_id = str(cve_id).strip()

                    if '_cve-' in clean_cve_id.lower():
                        parts = clean_cve_id.lower().split('_cve-', 1)
                        if len(parts) > 1:
                            clean_cve_id = 'CVE-' + parts[1].upper()
                    elif clean_cve_id.upper().startswith('CVE-'):
                        clean_cve_id = clean_cve_id.upper()
                    else:
                        # 🔹 Se non è un vero CVE, salta subito
                        if debug:
                            print(f"   [CIRCL] {clean_cve_id} non è un CVE valido, salto...")
                        continue
                    
                    # Estrai descrizione con priorità alle strutture più dettagliate
                    description = ""
                    
                    # 1. Prova formato CVE 5.0 (containers.cna.descriptions)
                    if not description and 'containers' in cve_data:
                        try:
                            cna = cve_data.get('containers', {}).get('cna', {})
                            descs = cna.get('descriptions', [])
                            if isinstance(descs, list) and len(descs) > 0:
                                for desc_obj in descs:
                                    if isinstance(desc_obj, dict):
                                        val = desc_obj.get('value', '')
                                        # Preferisci descrizioni in inglese
                                        if desc_obj.get('lang') == 'en' or not description:
                                            description = val
                                            if desc_obj.get('lang') == 'en':
                                                break
                        except Exception:
                            pass
                    
                    # 2. Prova array descriptions diretto (formato NVD/FKIE)
                    if not description and 'descriptions' in cve_data:
                        try:
                            descs = cve_data.get('descriptions', [])
                            if isinstance(descs, list) and len(descs) > 0:
                                for desc_obj in descs:
                                    if isinstance(desc_obj, dict):
                                        val = desc_obj.get('value', '')
                                        # Preferisci descrizioni in inglese
                                        if desc_obj.get('lang') == 'en' or not description:
                                            description = val
                                            if desc_obj.get('lang') == 'en':
                                                break
                        except Exception:
                            pass
                    
                    # 3. Campi diretti summary/description
                    if not description:
                        description = (
                            cve_data.get("summary") or 
                            cve_data.get("description") or 
                            cve_data.get("Description") or 
                            ""
                        )
                    
                    # 4. Cerca in strutture nested
                    if not description:
                        try:
                            if 'cve' in cve_data and isinstance(cve_data['cve'], dict):
                                cve_nested = cve_data['cve']
                                description = (
                                    cve_nested.get('description') or 
                                    cve_nested.get('summary') or 
                                    ""
                                )
                        except Exception:
                            pass
                    
                    # Estrai CVSS
                    cvss = extract_cvss_from_cve(cve_data)
                    
                    # OUTPUT UNIFORME
                    # if debug:
                    #     cvss_str = f"CVSS:{cvss:.1f}" if cvss else "NO CVSS"
                    #     print(f"   [CIRCL] {clean_cve_id} - {cvss_str}")
                    #     if description:
                    #         print(f"         {description[:100]}...")
                    
                    result_obj = {
                        "id": clean_cve_id,
                        "cve": clean_cve_id,
                        "cvss": cvss,
                        "summary": description,
                        "description": description,
                        "source": source,
                        "original_id": cve_id if cve_id != clean_cve_id else None,
                        "raw": cve_data,
                    }
                    
                    results.append(result_obj)
                    
                    
                except Exception:
                    continue
        final_cves = {}
        
        for cve in results:
            cve_id = cve['id']
            
            if cve_id not in final_cves:
                final_cves[cve_id] = cve
            else:
                # Merge: mantieni miglior CVSS e descrizione più lunga
                existing = final_cves[cve_id]
                if cve.get('cvss') is not None and existing.get('cvss') is None:
                    existing['cvss'] = cve['cvss']
                if cve.get('summary') and len(cve.get('summary', '')) > len(existing.get('summary', '')):
                    existing['summary'] = cve['summary']
                    existing['description'] = cve['description']
        
        results = list(final_cves.values())
        
            
        if debug:
            for cve in results:
                cvss_str = f"CVSS:{cve['cvss']:.1f}" if cve.get('cvss') else "NO CVSS"
                print(f"   [CIRCL] {cve['id']} - {cvss_str}")
                desc = cve.get('summary', '')  if cve.get('summary') else "NO DESC"
                if desc:
                    print(f"         {desc[:100]}...")


        if results and version:
            filtered = filter_results_by_version(results, version, product, debug=debug)
            if filtered["filtered_out"] > 0:
                print(f"   [CIRCL] Filtro versione: {filtered['total_before']} -> {filtered['total_after']} specifici per v{version}")
            return filtered["filtered_results"]
        
        return results
        
    except Exception as e:
        if debug:
            print(f"   [CIRCL] ERRORE: {e}")
        return []
    
# -------------------------
# Query OSV
# -------------------------
def query_osv(product: str, version=None, debug=False) -> list:
    """Query OSV con estrazione CVE da related/upstream"""
    try:
        payload = {"package": {"name": product}}
        if version:
            payload["version"] = version
        #osv accetta solo post
        r = requests.post("https://api.osv.dev/v1/query", headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 400:
            return []
        r.raise_for_status()

        data = r.json()
        results = []
        
        if isinstance(data, dict):
            results = data.get("vulns", []) or data.get("results", [])
        elif isinstance(data, list):
            results = data
        
        # Estrai CVE da related e upstream
        extracted_cves = []
        for item in results:
            # Estrai CVE da related e upstream
            cve_list = item.get("related", []) + item.get("upstream", [])
            cvss_str=extract_cvss_from_cve(item)
            
            for cve_code in cve_list:
                if cve_code.upper().startswith("CVE-"):
                    cve_upper = cve_code.upper()
                    
                    # OUTPUT UNIFORME
                    if debug:
                        # cvss_str = "NO CVSS"  # OSV non fornisce CVSS
                        print(f"   [OSV] {cve_upper} - {cvss_str}")
                        if item.get("summary"):
                            print(f"         {item['summary'][:100]}...")
                    
                    extracted_cves.append({
                        "id": cve_upper,
                        "cvss": None,  # OSV non fornisce CVSS numerico
                        "summary": item.get("summary", ""),
                        "raw": item
                    })
        
        return extracted_cves
        
    except:
        return []

# -------------------------
# Ricerca completa
# -------------------------

def search_single(vendor, product, version, debug=False):
    """Ricerca su OSV, CIRCL, NVD con output uniformi"""

    out = {
        "vendor": vendor,
        "product": product,
        "version": version,
        "osv": [],
        "circl": [],
        "circl_unfiltered": [],  # 🆕 Risultati PRIMA del filtraggio
        "nvd": []
    }

    # --- OSV ---
    osv_results = query_osv(product, version, debug=debug)
    print("\n")
    out["osv"] = [{"query": f"{vendor}/{product}", "hits": osv_results}]
    
    if osv_results:
        print(f"   [OSV] {len(osv_results)} risultati trovati")
    else:
        print(f"   [OSV] Nessun risultato trovato")

    # --- CIRCL ---
    # Prima ottieni TUTTI i risultati senza filtraggio
    circl_all_results = query_circl(vendor, product, version=None, debug=False)
    out["circl_unfiltered"] = [{"query": f"{vendor}/{product}", "hits": circl_all_results}]
    
    # Poi ottieni i risultati filtrati (con debug)
    circl_results = query_circl(vendor, product, version, debug=debug)
    out["circl"] = [{"query": f"{vendor}/{product}", "hits": circl_results}]
    
    if circl_results:
        print(f"   [CIRCL] {len(circl_results)} risultati trovati")
    else:
        print(f"   [CIRCL] Nessun risultato trovato")

    # --- NVD ---
    nvd_results = smart_nvd_search(product, vendor, version, debug=debug)
    out["nvd"] = [{"query": f"{vendor}/{product}", "hits": nvd_results}]
    if nvd_results:
        print(f"   [NVD] {len(nvd_results)} risultati trovati")
    else:
        print(f"   [NVD] Nessun risultato trovato")

    return out

 
# -------------------------
# Output
# -------------------------

def save_csv(rows, fname):
    fields = ["vendor", "product", "version", "model", "ip", "max_cvss", "avg_cvss", "cve_ids"]
    
    # Usa punto e virgola come separatore per compatibilità Excel Italia
    with open(fname, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        
        for r in rows:
            # Formatta CVE IDs come stringa separata da virgole (dentro la cella)
            cve_ids_str = ", ".join(r.get("cve_ids", []))
            
            w.writerow({
                "vendor": r.get("vendor", ""),
                "product": r.get("product", ""),
                "version": r.get("version", ""),
                "model": r.get("model", ""),
                "ip": r.get("ip", ""),
                "max_cvss": f"{r.get('top_cvss'):.1f}" if r.get('top_cvss') else "",
                "avg_cvss": f"{r.get('avg_cvss'):.2f}" if r.get('avg_cvss') else "",
                "cve_ids": cve_ids_str
            })
    
    print(f"CSV salvato: {fname}")

def print_summary(results):
    print("\n" + "="*60)
    print("RIASSUNTO FINALE")
    print("="*60)
    
    total_cves = len(set(cve for r in results for cve in r.get('cve_ids', [])))
    
    all_cvss_scores = []
    for r in results:
        all_cvss_scores.extend(r.get('cvss_scores', []))
    
    no_version = sum(1 for r in results if not r.get('version'))
    
    print(f"CVE unici totali: {total_cves}")
    print(f"Dispositivi analizzati: {len(results)}")
    
    if all_cvss_scores:
        print(f"\nSTATISTICHE GLOBALI:")
        print(f"   CVSS massimo: {max(all_cvss_scores):.1f}")
        print(f"   CVSS medio: {sum(all_cvss_scores)/len(all_cvss_scores):.2f}")
        print(f"   CVE con CVSS: {len(all_cvss_scores)}/{total_cves} ({len(all_cvss_scores)/total_cves*100:.1f}%)")
        
        critical = sum(1 for s in all_cvss_scores if s >= 9.0)
        high = sum(1 for s in all_cvss_scores if 7.0 <= s < 9.0)
        medium = sum(1 for s in all_cvss_scores if 4.0 <= s < 7.0)
        low = sum(1 for s in all_cvss_scores if s < 4.0)
        
        print(f"\n   Distribuzione severita globale:")
        if critical > 0:
            print(f"      CRITICO (>=9.0): {critical}")
        if high > 0:
            print(f"      ALTO (7.0-8.9): {high}")
        if medium > 0:
            print(f"      MEDIO (4.0-6.9): {medium}")
        if low > 0:
            print(f"      BASSO (<4.0): {low}")
        
        print(f"\nSTATISTICHE PER DISPOSITIVO:")
        print(f"{'_'*60}")
        for i, r in enumerate(results, 1):
            device_name = f"{r.get('vendor') or 'NO_VENDOR'} {r.get('product')}"
            if r.get('version'):
                device_name += f" v{r['version']}"
            
            cve_count = r.get('cve_count', 0)
            cvss_scores = r.get('cvss_scores', [])
            
            print(f"\n{i}. {device_name}")
            print(f"   CVE: {cve_count} totali, {len(cvss_scores)} con CVSS")
            
            if cvss_scores:
                print(f"   CVSS: MAX={r.get('top_cvss'):.1f} | AVG={r.get('avg_cvss'):.2f}")
                
                severity_items = []
                if r.get('critical_count', 0) > 0:
                    severity_items.append(f"CRITICO:{r['critical_count']}")
                if r.get('high_count', 0) > 0:
                    severity_items.append(f"ALTO:{r['high_count']}")
                if r.get('medium_count', 0) > 0:
                    severity_items.append(f"MEDIO:{r['medium_count']}")
                if r.get('low_count', 0) > 0:
                    severity_items.append(f"BASSO:{r['low_count']}")
                
                if severity_items:
                    print(f"   Severita: {' | '.join(severity_items)}")
            else:
                print(f"   Nessun CVSS disponibile")
            
            if r.get('version_warning'):
                print(f"   ATTENZIONE: {r['version_warning']}")
        
        print(f"\n{'_'*60}")
        devices_with_cvss = [r for r in results if r.get('top_cvss')]
        if devices_with_cvss:
            most_critical = max(devices_with_cvss, key=lambda x: x.get('top_cvss', 0))
            most_vulnerable = max(devices_with_cvss, key=lambda x: x.get('critical_count', 0))
            
            critical_name = f"{most_critical.get('vendor') or 'NO_VENDOR'} {most_critical.get('product')}"
            print(f"DISPOSITIVO PIU CRITICO (CVSS): {critical_name}")
            print(f"   CVSS MAX: {most_critical.get('top_cvss'):.1f}")
            
            if most_vulnerable != most_critical:
                vuln_name = f"{most_vulnerable.get('vendor') or 'NO_VENDOR'} {most_vulnerable.get('product')}"
                print(f"\nPIU VULNERABILITA CRITICHE: {vuln_name}")
                print(f"   CVE critici: {most_vulnerable.get('critical_count', 0)}")
        
    else:
        print(f"Nessun CVSS disponibile nei risultati")
    
    if no_version > 0:
        print(f"\nATTENZIONE:")
        print(f"   {no_version}/{len(results)} dispositivi analizzati SENZA versione")
        print(f"   Raccomandazione: aggiorna inventario con versioni specifiche")
    
    print("="*60)

def process_search_results(res, vendor, product, version, model="", ip=""):
    """Processa i risultati di search_single() e restituisce il dizionario finale"""
    cve_dict = {}
    cve_descr={}
    
    # === NVD ===
    for block in res.get("nvd", []):
        for h in block.get("hits", []):
            cve_id = h.get("id") or h.get("cve")
            if cve_id:
                cve_dict[cve_id] = h.get("cvss")
                cve_descr[cve_id] = h.get("summary") or h.get("description")

    
    # === CIRCL ===
    for block in res.get("circl", []):
        for h in block.get("hits", []):
            cve_id = h.get("id") or h.get("cve")
            if cve_id and cve_id not in cve_dict:
                cve_dict[cve_id] = h.get("cvss")
                cve_descr[cve_id] = h.get("summary") or h.get("description")
    
    # === OSV ===
    for block in res.get("osv", []):
        for h in block.get("hits", []):
            cve_id = h.get("id") or (h.get("aliases") or [None])[0]
            if cve_id and cve_id not in cve_dict:
                cve_dict[cve_id] = h.get("cvss")
                cve_descr[cve_id] = h.get("summary") or h.get("description")
    
    # === CALCOLO STATISTICHE ===
    cvss_scores = [score for score in cve_dict.values() if score is not None]
    cve_description=[score for score in cve_descr.values() if score is not None]
    #  # DEBUG: Mostra quali CVE hanno/non hanno CVSS
    # print("\n=== DEBUG CVE DICT ===")
    # for cve_id, cvss in sorted(cve_dict.items()):
    #     print(f"   {cve_id}: {f'CVSS:{cvss:.1f}' if cvss else 'NO CVSS'}")
    # print("===================\n")
    
    top_cvss = max(cvss_scores) if cvss_scores else None
    avg_cvss = sum(cvss_scores) / len(cvss_scores) if cvss_scores else None
    
    critical = sum(1 for s in cvss_scores if s >= 9.0)
    high = sum(1 for s in cvss_scores if 7.0 <= s < 9.0)
    medium = sum(1 for s in cvss_scores if 4.0 <= s < 7.0)
    low = sum(1 for s in cvss_scores if s < 4.0)
    
    # === RITORNA DIZIONARIO ===
    return {
        "vendor": vendor,
        "product": product,
        "version": version,
        "model": model,
        "ip": ip,
        "cve_count": len(cve_dict),
        "cve_ids": list(cve_dict.keys()),
        "cvss_scores": cvss_scores,
        "cve_descriptions": cve_description,
        "top_cvss": top_cvss,
        "avg_cvss": avg_cvss,
        "critical_count": critical,
        "high_count": high,
        "medium_count": medium,
        "low_count": low,
        "version_warning": "NO VERSION" if not version else "",
        "full": res
    }


# -------------------------
# Main
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Ricerca vulnerabilita dispositivi biomedicali - CVSS FIXED")
    parser.add_argument("--csv", help="File CSV input")
    parser.add_argument("--vendor", help="Vendor")
    parser.add_argument("--product", help="Product")
    parser.add_argument("--version", help="Version")
    parser.add_argument("--debug", action="store_true", help="Enable debug output for version filtering")
    args = parser.parse_args()
    
    if args.csv:
        if not os.path.exists(args.csv):
            print(f"File non trovato: {args.csv}")
            return []
        
        results = []
        
        with open(args.csv, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
            total = len(rows)
            
            print(f"\nAnalisi di {total} dispositivi...\n")
            
            for i, row in enumerate(rows, 1):
                # Estrazione campi
                vendor = next((row[k].strip() for k in row if 'vendor' in k.lower() and row[k]), None)
                product = next((row[k].strip() for k in row if 'product' in k.lower() and row[k]), None)
                version = next((row[k].strip() for k in row if 'version' in k.lower() and row[k]), None)
                model = next((row[k].strip() for k in row if 'model' in k.lower() and row[k]), None)
                ip = next((row[k].strip() for k in row if 'ip' in k.lower() and row[k]), None)

                # Validazione
                if not product:
                    print(f"Riga {i} saltata (product mancante)")
                    continue
                
                vendor = vendor if vendor and vendor.lower() not in ["", "none", "null"] else None
                version = version if version and version.lower() not in ["", "none", "null"] else None
                
                device_name = f"{vendor or 'NO_VENDOR'} {product}"
                print(f"[{i}/{total}] {device_name}")
                version_status = f"v{version}" if version else "NO VERSION (possibili falsi positivi)"
                print(f"   Versione target: {version_status}")
                
                # Ricerca vulnerabilità 
                res = search_single(vendor, product, version, debug=args.debug)
                
                # PROCESSA RISULTATI (funzione unica)
                result = process_search_results(res, vendor, product, version, model, ip)
                
                # Output
                version_note = f" per v{version}" if version else " (tutte le versioni)"
                print(f"   Trovati {result['cve_count']} CVE unici{version_note} ({len(result['cvss_scores'])} con CVSS)")
                
                if result['cvss_scores']:
                    print(f"   CVSS dispositivo: MAX={result['top_cvss']:.1f} | AVG={result['avg_cvss']:.2f}")
                print()
                
                results.append(result)
                time.sleep(0.5)
    elif args.product:
        print(f"\nRicerca singola: {args.vendor or 'NO_VENDOR'} {args.product}\n")
        res = search_single(args.vendor, args.product, args.version, debug=args.debug)
        
        # PROCESSA RISULTATI (stessa funzione!)
        result = process_search_results(res, args.vendor, args.product, args.version)
        
        results = [result]  # Lista con un solo elemento
 
    
    if results:
        print_summary(results)
        with open(f"vuln_results.json", "w", encoding="utf-8") as f:
            json.dump({"results": results}, f, ensure_ascii=False, indent=2)
        print(f"JSON salvato: vuln_results.json")
        save_csv(results, f"vuln_summary.csv")
        save_circl_descriptions(results, "circl_descriptions.json")


if __name__ == "__main__":
    main()