#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
import os

# Ajouter le répertoire parent au chemin Python pour trouver les modules Odoo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from odoo import api, SUPERUSER_ID
from odoo.cli import server

_logger = logging.getLogger(__name__)

def fix_client_access(db_name, email=None):
    """Répare l'accès au parc IT pour un client identifié par son email.
    
    Si aucun email n'est fourni, corrige tous les clients qui ont une demande
    de service en état payé mais dont l'accès au parc n'est pas activé.
    """
    with api.Environment.manage():
        registry = server.odoo.registry(db_name)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            
            # Trouver les partenaires à corriger
            domain = []
            if email:
                domain = [('email', '=', email)]
                _logger.info(f"Recherche du client avec l'email: {email}")
            
            partners = env['res.partner'].search(domain)
            _logger.info(f"Nombre de partenaires trouvés: {len(partners)}")
            
            # Vérifier si le client a une demande de service active et payée
            for partner in partners:
                _logger.info(f"Traitement de {partner.name} (ID: {partner.id})")
                
                # Vérifier les demandes de service
                service_requests = env['it.service.request'].search([
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ['paid', 'contract_created'])
                ])
                
                if service_requests:
                    _logger.info(f"Demandes de service payées trouvées: {len(service_requests)}")
                    
                    # Vérifier si le contrat existe
                    contracts = env['it.contract'].search([
                        ('partner_id', '=', partner.id),
                        ('state', '!=', 'cancelled')
                    ])
                    
                    if contracts:
                        _logger.info(f"Contrats trouvés: {len(contracts)}")
                        
                        # Mettre à jour les indicateurs d'accès du partenaire
                        partner.write({
                            'is_it_client': True,
                            'is_it_client_approved': True,
                            'is_it_contract_paid': True,
                            'is_it_client_pending': False
                        })
                        _logger.info(f"✅ Accès activé pour {partner.name}")
                    else:
                        # Créer un contrat si nécessaire
                        _logger.warning(f"⚠️ Pas de contrat trouvé pour {partner.name} malgré un paiement effectué")
                        for request in service_requests:
                            if not request.contract_id:
                                try:
                                    _logger.info(f"Tentative de création d'un contrat pour {partner.name}")
                                    request.action_create_contract()
                                    
                                    # Mettre à jour l'accès du partenaire
                                    partner.write({
                                        'is_it_client': True,
                                        'is_it_client_approved': True,
                                        'is_it_contract_paid': True,
                                        'is_it_client_pending': False
                                    })
                                    _logger.info(f"✅ Contrat créé et accès activé pour {partner.name}")
                                except Exception as e:
                                    _logger.error(f"❌ Erreur lors de la création du contrat: {str(e)}")
                            else:
                                _logger.info(f"Un contrat existe déjà pour cette demande: {request.contract_id.name}")
                else:
                    _logger.warning(f"⚠️ Aucune demande de service payée trouvée pour {partner.name}")
                    
                    # Vérifier si d'autres indicateurs sont positifs
                    if partner.has_accepted_proposal:
                        _logger.info(f"Le partenaire a accepté une proposition, vérification des demandes...")
                        pending_requests = env['it.service.request'].search([
                            ('partner_id', '=', partner.id), 
                            ('state', 'in', ['proposal_accepted', 'invoiced'])
                        ])
                        
                        if pending_requests:
                            _logger.info(f"Demandes en attente trouvées: {len(pending_requests)}")
                            for request in pending_requests:
                                _logger.info(f"Forçage du statut 'payé' pour la demande {request.name}")
                                request.write({'state': 'paid'})
                                try:
                                    request.action_create_contract()
                                    
                                    # Mettre à jour l'accès du partenaire
                                    partner.write({
                                        'is_it_client': True,
                                        'is_it_client_approved': True,
                                        'is_it_contract_paid': True,
                                        'is_it_client_pending': False
                                    })
                                    _logger.info(f"✅ Contrat créé et accès activé pour {partner.name}")
                                except Exception as e:
                                    _logger.error(f"❌ Erreur lors de la création du contrat: {str(e)}")
            
            # Forcer l'activation des partenaires sans demande de service
            if email:
                if not partners:
                    _logger.warning(f"⚠️ Aucun partenaire trouvé avec l'email {email}")
                else:
                    partner = partners[0]
                    _logger.info(f"Forçage de l'accès pour {partner.name} sans vérification des demandes")
                    partner.write({
                        'is_it_client': True,
                        'is_it_client_approved': True,
                        'is_it_contract_paid': True,
                        'is_it_client_pending': False
                    })
                    _logger.info(f"✅ Accès forcé pour {partner.name}")
            
            cr.commit()
            _logger.info("Opération terminée avec succès.")

if __name__ == "__main__":
    # Configuration du logger
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    
    if len(sys.argv) < 2:
        print("Usage: python3 fix_client_access.py DB_NAME [EMAIL]")
        sys.exit(1)
    
    db_name = sys.argv[1]
    email = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_client_access(db_name, email) 