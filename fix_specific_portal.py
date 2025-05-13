#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import sys

def fix_specific_indentation():
    """
    Corriger spécifiquement le problème d'indentation à la ligne 825 mentionné dans l'erreur.
    """
    # Utiliser le chemin absolu
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(base_dir, 'custom_addons', 'it__park', 'controllers', 'portal.py')
    
    print(f"Recherche du fichier: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERREUR: Le fichier {file_path} n'existe pas!")
        # Essayer un autre chemin - celui où le script est exécuté
        current_dir = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(current_dir, '..', 'controllers', 'portal.py')
        file_path = os.path.normpath(file_path)
        print(f"Essai avec un autre chemin: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"ERREUR: Le fichier {file_path} n'existe pas non plus!")
            return False
    
    # Lire le contenu du fichier ligne par ligne
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Trouver la ligne avec 'try:' et vérifier la ligne suivante
    fixed = False
    for i in range(len(lines) - 1):
        if 'try:' in lines[i] and not lines[i + 1].startswith(' '):
            # Ajouter l'indentation à la ligne suivante
            lines[i + 1] = '    ' + lines[i + 1]
            fixed = True
            print(f"Indentation corrigée à la ligne {i + 1}")
    
    # Écrire les modifications dans le fichier
    if fixed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Corrections appliquées au fichier {file_path}")
    else:
        print("Aucun problème d'indentation trouvé")
        
    return fixed

if __name__ == "__main__":
    fix_specific_indentation() 