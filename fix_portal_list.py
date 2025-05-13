#!/usr/bin/env python
from odoo import api, SUPERUSER_ID

def modify_domain():
    """Corrige le domaine de recherche des tickets dans le portail"""
    filepath = "custom_addons/it__park/controllers/portal.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    import re
    # Trouver et remplacer le domaine de recherche des tickets
    pattern = r"domain = \[
\s+\('partner_id', '=', partner\.commercial_partner_id\.id\)
\s+\]"
    new_domain = "domain = ['|',\n            ('client_id', '=', partner.id),\n            ('partner_id', '=', partner.id)\n        ]"
    modified = re.sub(pattern, new_domain, content)
    
    if modified != content:
        with open(filepath, 'w') as f:
            f.write(modified)
        print("Domaine de recherche des tickets mis a jour")
        return True
    else:
        print("Impossible de mettre a jour le domaine de recherche")
        return False

if __name__ == "__main__":
    modify_domain()
