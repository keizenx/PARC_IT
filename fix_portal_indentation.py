#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def fix_portal_indentation():
    """
    Corrige l'erreur d'indentation dans le fichier portal.py qui cause l'échec de chargement du module.
    L'erreur est une ligne qui n'est pas indentée correctement après une instruction try.
    """
    portal_file = os.path.join('custom_addons', 'it__park', 'controllers', 'portal.py')
    
    # Vérifier si le fichier existe
    if not os.path.isfile(portal_file):
        print(f"Erreur: Le fichier {portal_file} n'existe pas.")
        return False
    
    # Lire le contenu du fichier
    with open(portal_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rechercher le bloc problématique et le corriger
    pattern = r'try:\s*\n([ ]*)([^\s])'
    fixed_content = re.sub(pattern, r'try:\n\1    \2', content)
    
    # Si aucun changement n'a été fait, tenter une correction plus spécifique
    if content == fixed_content:
        # Rechercher l'erreur "try: # Vérifier si l'utilisateur a déjà une demande active\n        partner = request.env.user.partner_id"
        pattern = r'try:\s*\n[ ]*# Vérifier si l\'utilisateur a déjà une demande active\s*\n[ ]*partner ='
        if re.search(pattern, content):
            # Correction spécifique pour cette erreur
            fixed_content = re.sub(
                r'try:\s*\n([ ]*)# Vérifier si l\'utilisateur a déjà une demande active\s*\n([ ]*)partner =',
                r'try:\n\1    # Vérifier si l\'utilisateur a déjà une demande active\n\2    partner =',
                content
            )
    
    # Si aucun changement n'a été fait, tenter une autre correction spécifique
    if content == fixed_content:
        # Chercher tous les blocs try sans indentation correcte
        pattern = r'try:\s*\n([ ]*)([^\s# ])'
        fixed_content = re.sub(pattern, r'try:\n\1    \2', content)
    
    # Si des changements ont été effectués, écrire dans le fichier
    if content != fixed_content:
        with open(portal_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Le fichier {portal_file} a été corrigé avec succès.")
        return True
    else:
        print(f"Aucune erreur d'indentation n'a été trouvée dans le format attendu.")
        return False

if __name__ == "__main__":
    fix_portal_indentation() 