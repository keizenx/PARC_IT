#!/bin/bash
# Script pour corriger les menus dupliqués du module it__park

ODOO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_SCRIPT="import odoo
import sys
sys.path.append('$ODOO_DIR')
from odoo.api import Environment
from odoo import SUPERUSER_ID
import importlib
import it__park.fix_duplicate_menus

with odoo.api.Environment.manage():
    with odoo.registry('Parc_IT_2').cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {})
        importlib.reload(it__park.fix_duplicate_menus)
        it__park.fix_duplicate_menus.fix_duplicate_menus(env)
        cr.commit()
"

echo "Correction des menus dupliqués du module it__park..."
cd "$ODOO_DIR"
python -c "$PYTHON_SCRIPT"
echo "Terminé. Veuillez rafraîchir votre navigateur pour voir les modifications." 