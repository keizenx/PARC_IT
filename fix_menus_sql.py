# -*- coding: utf-8 -*-

def fix_duplicate_menus(env):
    """
    Script simple pour corriger les menus dupliqués.
    À exécuter directement depuis le shell Odoo.
    """
    print("====== DÉBUT DE LA CORRECTION DES MENUS DUPLIQUÉS ======")
    
    # Liste des noms de menus problématiques
    menu_names = ['Logiciels', 'Licences', 'Contrats', 'Incidents', 'Interventions', 'Tickets IT', 'Tickets Helpdesk']
    
    for name in menu_names:
        # Trouver tous les menus avec ce nom
        menus = env['ir.ui.menu'].search([('name', '=', name), ('active', '=', True)])
        
        if len(menus) > 1:
            print(f"\n✓ Menu '{name}' : {len(menus)} occurrences trouvées")
            
            # Garder le premier, désactiver les autres
            keep_menu = menus[0]
            print(f"  - Conservé: ID={keep_menu.id}, parent={keep_menu.parent_id.name if keep_menu.parent_id else 'None'}")
            
            for menu in menus[1:]:
                print(f"  - Désactivé: ID={menu.id}, parent={menu.parent_id.name if menu.parent_id else 'None'}")
                
                # Désactiver directement dans la base de données avec SQL pour éviter les problèmes
                env.cr.execute(f"UPDATE ir_ui_menu SET active = FALSE WHERE id = {menu.id}")
                
                # Supprimer aussi les relations menu-groupe pour ce menu
                env.cr.execute(f"DELETE FROM ir_ui_menu_group_rel WHERE menu_id = {menu.id}")
        else:
            print(f"✓ Menu '{name}' : OK (pas de duplication)")
    
    # Vider le cache des menus
    env['ir.ui.menu'].clear_caches()
    print("\n====== FIN DE LA CORRECTION DES MENUS DUPLIQUÉS ======")
    print("\nRedémarrez votre serveur Odoo pour que les changements prennent effet.")
    
    return True

# Pour l'exécution dans le shell Odoo, copier-coller les lignes suivantes:
"""
import importlib
import sys
sys.path.append('C:/Users/franc/Desktop/odoo-18.0(community)/custom_addons')
import it__park.fix_menus_sql
importlib.reload(it__park.fix_menus_sql)
it__park.fix_menus_sql.fix_duplicate_menus(env)
""" 