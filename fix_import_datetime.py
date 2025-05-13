#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

def fix_datetime_import():
    """
    Ajoute l'import datetime manquant dans le fichier it_ticket.py
    """
    # Chemin du fichier models/it_ticket.py
    ticket_file_path = os.path.join('models', 'it_ticket.py')
    
    if not os.path.exists(ticket_file_path):
        print(f"Erreur: Impossible de trouver le fichier {ticket_file_path}")
        return False
    
    # Lire le contenu du fichier
    with open(ticket_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Recherche les imports existants et ajoute datetime s'il n'existe pas déjà
    import_pattern = r'(from odoo import.*?\nimport.*?\n)'
    
    if 'from datetime import datetime' in content:
        print("L'import datetime est déjà présent.")
        return True
    
    if 'from datetime import' in content:
        # Il y a déjà un import de datetime mais pas datetime directement
        modified_content = re.sub(
            r'from datetime import (.*?)\n',
            r'from datetime import \1, datetime\n',
            content
        )
    else:
        # Ajouter l'import après les imports existants
        if 'import logging' in content:
            modified_content = content.replace(
                'import logging',
                'import logging\nfrom datetime import datetime'
            )
        else:
            # Ajout après les imports de odoo
            modified_content = re.sub(
                import_pattern,
                r'\1from datetime import datetime\n\n',
                content
            )
    
    # Sauvegarder une copie du fichier original
    backup_path = ticket_file_path + '.datetime.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fichier de sauvegarde créé: {backup_path}")
    
    # Écrire le contenu modifié
    with open(ticket_file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    print("Import datetime ajouté avec succès.")
    
    return True

if __name__ == "__main__":
    print("Correction des imports...")
    if fix_datetime_import():
        print("Les modifications ont été appliquées. Redémarrez le serveur Odoo.")
    else:
        print("Aucune modification n'a été appliquée.") 