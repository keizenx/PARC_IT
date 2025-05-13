#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def fix_portal_file():
    """
    Corrige l'indentation de la méthode portal_create_incident à la ligne 187.
    """
    # Chemin absolu vers le fichier portal.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'controllers', 'portal.py')
    
    print(f"Tentative de correction du fichier: {file_path}")
    
    # Lire le contenu du fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Identifier la classe ITPortal et son niveau d'indentation
    class_indent = ""
    class_line = -1
    for i, line in enumerate(lines):
        if "class ITPortal" in line:
            class_line = i
            break
    
    # Trouver le niveau d'indentation de base pour les méthodes dans cette classe
    method_indent = ""
    for i in range(class_line+1, len(lines)):
        if re.match(r'^\s+def\s+', lines[i]):
            method_indent = re.match(r'^(\s+)', lines[i]).group(1)
            break
    
    # Trouver la méthode portal_create_incident et corriger son indentation
    target_line = -1
    for i, line in enumerate(lines):
        if "def portal_create_incident" in line:
            target_line = i
            break
    
    if target_line != -1:
        # Vérifier et corriger l'indentation
        current_indent = re.match(r'^(\s*)', lines[target_line]).group(1)
        if current_indent != method_indent:
            print(f"Correction de l'indentation à la ligne {target_line+1}")
            lines[target_line] = method_indent + lines[target_line].lstrip()
            
            # Ajuster l'indentation du bloc de code de la méthode
            block_indent = method_indent + "    "
            i = target_line + 1
            while i < len(lines) and (lines[i].strip() == "" or lines[i].startswith(current_indent + " ")):
                if lines[i].strip() != "":
                    lines[i] = block_indent + lines[i].lstrip()
                i += 1
    
    # Écrire les changements dans le fichier
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Correction terminée.")

if __name__ == "__main__":
    fix_portal_file() 