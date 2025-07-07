# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DocumentsPack(Document):

    def create_envelope(self, reference_doctype=None, reference_link=None):
        return frappe.get_doc(
            {
                "doctype": "Envelope",
                "from_pack": self.name,
                "subject": self.subject,
                "reference_doctype": reference_doctype,
                "reference_link": reference_link,
                "document_templates": [
                    {"document_template": doc_template.document_template}
                    for doc_template in self.document_templates
                ],
            }
        ).insert()
