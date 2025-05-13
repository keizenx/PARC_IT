#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

def fix_portal_indentation():
    """Corrige l'indentation de la méthode portal_create_incident dans portal.py"""
    
    # Chemin du fichier
    portal_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'controllers', 'portal.py')
    
    print(f"Correction de {portal_file}")
    
    # Lire le contenu actuel
    with open(portal_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Normaliser les fins de ligne
    content = content.replace('\r\n', '\n')
    
    # Corriger l'indentation de la méthode portal_incident_detail
    # Rechercher le bloc problématique
    start_pattern = "        try:\n            incident_sudo = self._document_check_access('it.incident', incident_id)"
    end_pattern = "            return request.redirect('/my/incidents')"
    values_block = "            values = {\n            'incident': incident_sudo,\n            'page_name': 'incident',\n            }\n            return request.render(\"it__park.portal_incident_detail\", values)"
    correct_values_block = "        values = {\n            'incident': incident_sudo,\n            'page_name': 'incident',\n        }\n        return request.render(\"it__park.portal_incident_detail\", values)"
    
    # Corriger l'indentation
    if start_pattern in content and end_pattern in content and values_block in content:
        content = content.replace(values_block, correct_values_block)
        print("Bloc 'values' corrigé.")
    
    # Corriger l'indentation de la méthode portal_create_incident
    route_decorator = "            @http.route(['/my/incidents/new'], type='http', auth=\"user\", website=True)"
    method_def = "    def portal_create_incident(self, **kw):"
    correct_route_decorator = "    @http.route(['/my/incidents/new'], type='http', auth=\"user\", website=True)"
    
    if route_decorator in content and method_def in content:
        content = content.replace(route_decorator, correct_route_decorator)
        print("Décorateur @http.route corrigé.")
    
    # Écrire le contenu corrigé
    with open(portal_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Correction d'indentation terminée.")

if __name__ == "__main__":
    fix_portal_indentation() 