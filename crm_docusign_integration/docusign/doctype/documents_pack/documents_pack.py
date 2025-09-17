# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DocumentsPack(Document):

    def before_save(self):
        self.validate_templates()

    def validate_templates(self):
        is_custom = None
        for template in self.document_templates:
            is_template_custom = frappe.db.get_value(
                "Document Template", template.document_template, "is_custom"
            )

            if is_custom is None:
                is_custom = is_template_custom or False
            elif is_custom != is_template_custom:
                frappe.throw(
                    "Templates can not be a mix of Custom and Non-Custom templates. They are required to be either of them."
                )

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
