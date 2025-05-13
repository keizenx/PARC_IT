#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
from datetime import datetime

def fix_notification_method():
    """
    Améliore la méthode _send_notification dans it_ticket.py pour s'assurer 
    que les emails sont envoyés correctement.
    """
    # Chemin du fichier models/it_ticket.py
    ticket_file_path = os.path.join('models', 'it_ticket.py')
    
    if not os.path.exists(ticket_file_path):
        print(f"Erreur: Impossible de trouver le fichier {ticket_file_path}")
        return False
    
    # Lire le contenu du fichier
    with open(ticket_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver la méthode _send_notification
    pattern = r'(def _send_notification\(self\):.*?""".*?""".*?)(.*?)(\n    def |$)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("La méthode _send_notification n'a pas été trouvée.")
        return False
    
    method_start = match.group(1)
    method_body = match.group(2)
    method_end = match.group(3)
    
    # Ajouter des logs supplémentaires et des optimisations à la méthode
    improved_method_body = method_body.replace(
        "# Créer et envoyer l'e-mail",
        """# Créer et envoyer l'e-mail
        print(f"[{datetime.now()}] Tentative d'envoi d'email pour le ticket {self.name} ({self.id})")"""
    )
    
    improved_method_body = improved_method_body.replace(
        "_logger.error(f\"Erreur lors de l'envoi de la notification par email: {str(e)}\")",
        """_logger.error(f"Erreur lors de l'envoi de la notification par email: {str(e)}")
                        print(f"[{datetime.now()}] ERREUR EMAIL: {str(e)}")"""
    )
    
    # Ajouter une notification directe en cas d'échec de l'envoi par mail
    improved_method_body = improved_method_body.replace(
        "# Marquer comme envoyé",
        """# Notification directe au browser même en cas d'échec de l'email
        try:
            # Créer une notification utilisateur directement dans Odoo
            title = f"Nouveau ticket: {self.name}"
            message = f"Un nouveau ticket a été créé par {self.client_id.name}\\nRéférence: {self.reference}\\nPriorité: {self.priority}"
            
            admin_users_ids = self.env['res.users'].sudo().search([
                ('groups_id', 'in', self.env.ref('it__park.group_it_admin').id)
            ]).ids
            
            if admin_users_ids:
                self.env['mail.bus']._sendmany([
                    (admin_id, 'mail.simple_notification', 
                     {'title': title, 'message': message, 'sticky': True, 'warning': True}) 
                    for admin_id in admin_users_ids
                ])
                print(f"[{datetime.now()}] Notifications en direct envoyées à {len(admin_users_ids)} administrateurs")
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de la notification directe: {str(e)}")
            print(f"[{datetime.now()}] ERREUR NOTIFICATION: {str(e)}")
        
        # Marquer comme envoyé"""
    )
    
    # Assembler le contenu modifié
    modified_content = content.replace(
        method_start + method_body + method_end,
        method_start + improved_method_body + method_end
    )
    
    # Sauvegarder une copie du fichier original
    backup_path = ticket_file_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fichier de sauvegarde créé: {backup_path}")
    
    # Écrire le contenu modifié dans le fichier
    with open(ticket_file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    print(f"Méthode _send_notification améliorée avec succès.")
    
    return True

def add_debug_to_submit_ticket():
    """
    Ajoute des logs à la méthode portal_submit_ticket pour vérifier l'envoi de notification.
    """
    # Chemin du fichier controllers/portal.py
    portal_file_path = os.path.join('controllers', 'portal.py')
    
    if not os.path.exists(portal_file_path):
        print(f"Erreur: Impossible de trouver le fichier {portal_file_path}")
        return False
    
    # Lire le contenu du fichier
    with open(portal_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rechercher la méthode portal_submit_ticket
    pattern = r'(def portal_submit_ticket.*?ticket = request\.env\[\'it\.ticket\'\]\.sudo\(\)\.create\(vals\))(.*?)(# Rediriger vers la page de remerciement)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("La méthode portal_submit_ticket n'a pas été trouvée dans le format attendu.")
        return False
    
    method_start = match.group(1)
    method_middle = match.group(2)
    method_end = match.group(3)
    
    # Ajouter des logs pour le débogage
    improved_middle = method_middle + """
        # Vérification explicite de l'envoi d'email
        print(f"Ticket #{ticket.id} créé avec succès. Envoi de notification...")
        
        # Forcer l'envoi immédiat pour éviter les problèmes de transaction
        self.env.cr.commit()
        """
    
    # Assembler le contenu modifié
    modified_content = content.replace(
        method_start + method_middle + method_end,
        method_start + improved_middle + method_end
    )
    
    # Sauvegarder une copie du fichier original si pas déjà fait
    backup_path = portal_file_path + '.email.bak'
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fichier de sauvegarde créé: {backup_path}")
    
    # Écrire le contenu modifié dans le fichier
    with open(portal_file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    print(f"Méthode portal_submit_ticket améliorée avec debug.")
    
    return True

if __name__ == "__main__":
    print("Amélioration de la notification par email...")
    notification_fixed = fix_notification_method()
    submit_improved = add_debug_to_submit_ticket()
    
    if notification_fixed or submit_improved:
        print("Des améliorations ont été apportées au système de notification.")
        print("Vérifiez également les paramètres du serveur SMTP dans les paramètres Odoo:")
        print("1. Allez à Configuration > Paramètres généraux")
        print("2. Dans la section 'Messagerie', vérifiez que le serveur de messagerie est correctement configuré")
        print("3. Vous pouvez aussi aller à Paramètres techniques > Email > Emails sortants pour voir les emails en échec")
        print("\nRedémarrez le serveur Odoo pour appliquer les changements.")
    else:
        print("Aucune modification n'a été appliquée.") 