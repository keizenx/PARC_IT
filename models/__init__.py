# -*- coding: utf-8 -*-

from . import models
from . import res_partner
from . import res_company
from . import res_users
from . import hr_employee
# Suppression de l'import de helpdesk qui cause une erreur d'importation circulaire
# Import des fichiers helpdesk_team et helpdesk_ticket plus tard dans le fichier
from . import it_equipment
from . import it_software
from . import it_license
from . import it_incident
from . import it_incident_type
from . import it_incident_category
from . import it_incident_priority
from . import it_intervention
from . import it_contract
from . import it_document
from . import it_dashboard
from . import it_sla
from . import account_inherit
# Commenté pour résoudre les erreurs liées aux dépendances stock manquantes
# from . import stock_inherit
# from . import stock_models
# from . import stock_move
from . import it_reporter
from . import it_ticket
# Import des fichiers liés à helpdesk après it_ticket pour éviter les imports circulaires
from . import helpdesk_ticket
from . import helpdesk_team
from . import it_service_type
from . import it_service_request
from . import ir_config_parameter
from . import ir_ui_menu
from . import res_config_settings
