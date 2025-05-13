# -*- coding: utf-8 -*-
# Script pour corriger les menus dupliqués - à exécuter depuis le shell Odoo

def run():
    """
    Lancez cette fonction depuis le shell Odoo avec:
    
    from it__park.run_menu_fix import run
    run()
    """
    import importlib
    from odoo import api, SUPERUSER_ID
    import it__park.fix_duplicate_menus
    
    print("Chargement du script de correction...")
    importlib.reload(it__park.fix_duplicate_menus)
    
    # Exécuter la correction avec l'environnement courant
    it__park.fix_duplicate_menus.fix_duplicate_menus(env)
    
    # Commit les changements
    env.cr.commit()
    
    print("\nCorrigé avec succès! Veuillez rafraîchir votre navigateur pour voir les changements.") 