# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DocuSignIntegration(Document):

    def before_save(self):

        # Make sure url doesn't ends with '/'
        if self.get("api_base_uri", default="").endswith("/"):
            self.update({"api_base_uri": self.get("api_base_uri")[0:-1]})

        # Set redirect_uri
        if not self.get("redirect_uri"):
            self.update(
                {
                    "redirect_uri": f"https://{frappe.local.site}/api/method/crm_docusign_integration.docusign.api.auth.verify_consent"
                }
            )
