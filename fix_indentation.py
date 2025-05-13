#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def fix_indentation():
    """
    Normalise l'indentation dans le fichier portal.py pour corriger les erreurs.
    """
    # Utiliser un chemin absolu pour le fichier portal.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'controllers', 'portal.py')
    
    print(f"Tentative d'ouverture du fichier: {file_path}")
    
    # Lire le contenu du fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Normaliser les fins de ligne
    content = content.replace('\r\n', '\n')
    
    # Diviser le fichier en lignes
    lines = content.split('\n')
    
    # Normaliser l'indentation
    fixed_lines = []
    in_class = False
    in_method = False
    in_try = False
    class_indent = ''
    method_indent = ''
    try_indent = ''
    
    for line in lines:
        # Détecter les définitions de classe
        if re.match(r'^class\s+\w+', line):
            in_class = True
            in_method = False
            in_try = False
            class_indent = ''
            fixed_lines.append(line)
            continue
        
        # Détecter les définitions de méthodes
        if in_class and re.match(r'^\s+def\s+\w+', line):
            in_method = True
            in_try = False
            method_indent = re.match(r'^(\s+)', line).group(1)
            fixed_lines.append(line)
            continue
        
        # Détecter les blocs try
        if in_method and re.match(r'^\s+try:', line):
            in_try = True
            try_indent = re.match(r'^(\s+)', line).group(1) + '    '
            fixed_lines.append(line)
            continue
        
        # Ligne vide
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # Lignes à l'intérieur d'un bloc try
        if in_try and not re.match(r'^\s+except\s+', line) and not re.match(r'^\s+finally:', line):
            # Vérifier si l'indentation est correcte
            if not line.startswith(try_indent) and line.strip() and not re.match(r'^\s+try:', line):
                # Corriger l'indentation
                line = try_indent + line.lstrip()
        
        fixed_lines.append(line)
    
    # Écrire le contenu corrigé dans le fichier
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"Indentation normalisée dans {file_path}")

if __name__ == "__main__":
    fix_indentation()
    print("Terminé.") 