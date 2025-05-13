#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re

def fix_portal_access():
    """
    Modifie le fichier portal.py pour désactiver temporairement la vérification d'accès,
    permettant à tous les utilisateurs connectés d'accéder aux tickets.
    """
    # Chemin du fichier controllers/portal.py
    portal_file_path = os.path.join('controllers', 'portal.py')
    
    if not os.path.exists(portal_file_path):
        print(f"Erreur: Impossible de trouver le fichier {portal_file_path}")
        return False
    
    # Lire le contenu du fichier
    with open(portal_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Motif pour trouver la méthode _check_it_park_access
    pattern = r'(def _check_it_park_access\(self\):.*?return )(.+?)(\n)'
    
    # Contenu modifié
    if re.search(pattern, content, re.DOTALL):
        modified_content = re.sub(pattern, r'\1True  # Désactivé temporairement - Retournait: \2\3', content, flags=re.DOTALL)
        
        # Sauvegarder une copie du fichier original
        backup_path = portal_file_path + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fichier de sauvegarde créé: {backup_path}")
        
        # Écrire le contenu modifié dans le fichier
        with open(portal_file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Méthode _check_it_park_access modifiée avec succès.")
        
        return True
    else:
        print("Avertissement: La méthode _check_it_park_access n'a pas été trouvée dans le format attendu.")
        return False

def fix_new_ticket_route():
    """
    Trouve le template XML qui contient le bouton 'Nouveau ticket' et corrige l'URL
    de '/my/tickets/new' à '/my/tickets/add'.
    """
    # Chemin probable du template
    template_file = os.path.join('views', 'it_support_ticket_list.xml')
    
    if not os.path.exists(template_file):
        print(f"Erreur: Impossible de trouver le fichier {template_file}")
        return False
    
    # Lire le contenu du fichier
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Motif pour trouver la balise <a> avec href="/my/tickets/new"
    pattern = r'(<a href=")(/my/tickets/new)(".*?>)'
    
    # Contenu modifié
    if re.search(pattern, content):
        modified_content = re.sub(pattern, r'\1/my/tickets/add\3', content)
        
        # Sauvegarder une copie du fichier original
        backup_path = template_file + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fichier de sauvegarde créé: {backup_path}")
        
        # Écrire le contenu modifié dans le fichier
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"URL du bouton 'Nouveau ticket' corrigée avec succès.")
        
        return True
    else:
        print("Avertissement: L'URL du bouton 'Nouveau ticket' n'a pas été trouvée dans le format attendu.")
        return False

if __name__ == "__main__":
    print("Correction de l'accès au portail des tickets...")
    access_fixed = fix_portal_access()
    route_fixed = fix_new_ticket_route()
    
    if access_fixed or route_fixed:
        print("Des modifications ont été apportées. Redémarrez le serveur Odoo pour appliquer les changements.")
    else:
        print("Aucune modification n'a été appliquée.") 