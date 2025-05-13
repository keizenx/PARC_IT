# -*- coding: utf-8 -*-

def fix_duplicate_menus(env):
    """
    Script pour corriger les menus dupliqués dans le module it__park
    """
    print("Début de la correction des menus dupliqués...")
    
    # Récupérer les noms de menus qui posent problème
    duplicate_menu_names = ['Logiciels', 'Licences', 'Contrats', 'Incidents', 'Interventions', 'Tickets IT', 'Tickets Helpdesk']
    
    # Trouver tous les menus avec ces noms
    menus = env['ir.ui.menu'].search([('name', 'in', duplicate_menu_names)])
    
    print(f"Trouvé {len(menus)} menus à vérifier")
    
    # Grouper les menus par nom
    grouped_menus = {}
    for menu in menus:
        if menu.name not in grouped_menus:
            grouped_menus[menu.name] = []
        grouped_menus[menu.name].append(menu)
    
    # Pour chaque groupe de menus, conserver le premier et désactiver les autres
    for name, menu_list in grouped_menus.items():
        if len(menu_list) > 1:
            print(f"Menu '{name}' : {len(menu_list)} occurrences trouvées")
            
            # Conserver le premier menu (celui défini dans it_park_menus.xml)
            keep_menu = menu_list[0]
            print(f"  - Conservation du menu ID={keep_menu.id}, parent={keep_menu.parent_id.name if keep_menu.parent_id else 'None'}")
            
            # Désactiver les autres (mettre active=False)
            for menu in menu_list[1:]:
                print(f"  - Désactivation du menu ID={menu.id}, parent={menu.parent_id.name if menu.parent_id else 'None'}")
                menu.active = False
                env.cr.execute(f"UPDATE ir_ui_menu SET active = FALSE WHERE id = {menu.id}")
    
    # Forcer le rafraîchissement du cache des menus
    env.cr.execute("DELETE FROM ir_ui_menu_group_rel WHERE menu_id NOT IN (SELECT id FROM ir_ui_menu WHERE active = TRUE)")
    env['ir.ui.menu'].clear_caches()
    
    print("Correction des menus dupliqués terminée avec succès !")
    return True

# Pour exécuter directement depuis le shell Odoo:
# env = self.env  # Dans le shell Odoo
# import importlib
# import sys
# sys.path.append('/path/to/custom_addons')
# import it__park.fix_duplicate_menus
# importlib.reload(it__park.fix_duplicate_menus)
# it__park.fix_duplicate_menus.fix_duplicate_menus(env) 