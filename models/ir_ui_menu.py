# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.modules.registry import Registry

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def clean_duplicate_menus(self):
        """Nettoie les menus dupliqués dans la base de données."""
        # Trouver les menus dupliqués basés sur le nom et le parent_id
        self.env.cr.execute("""
            WITH duplicate_menus AS (
                SELECT MIN(id) as original_id,
                       array_agg(id) as duplicate_ids,
                       name,
                       parent_id
                FROM ir_ui_menu
                GROUP BY name, parent_id
                HAVING COUNT(*) > 1
            )
            SELECT original_id, duplicate_ids
            FROM duplicate_menus;
        """)
        duplicates = self.env.cr.fetchall()

        for original_id, duplicate_ids in duplicates:
            # Convertir la liste des IDs en liste Python
            duplicate_list = list(duplicate_ids)
            # Retirer l'ID original de la liste des doublons
            duplicate_list.remove(original_id)
            
            if duplicate_list:
                # Supprimer les menus dupliqués
                self.browse(duplicate_list).unlink()

        # Utiliser la nouvelle méthode pour vider le cache
        Registry(self.env.cr.dbname).clear_cache()
        
        return True 