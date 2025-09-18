# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm_docusign_integration.docusign.integration.e_signature import send_envelope


class Envelope(Document):

    def before_save(self):
        self.validate_templates()

    def after_insert(self):
        documents = []
        template_data = []
        self.documents = []

        for idx, template in enumerate(self.document_templates):
            document_id = idx + 1  # Start ids with 1
            template_doc = frappe.get_doc(
                "Document Template", template.document_template
            )
            template_context = template_doc.get_document_context(
                self.reference_doctype, self.reference_link
            )

            if template_doc.is_custom:
                document_pdf = template_doc.generate_pdf(
                    self.reference_doctype, self.reference_link
                )

                file_name = template.document_template
                if self.reference_doctype:
                    file_name = file_name + f"-{self.reference_doctype}"
                if self.reference_link:
                    file_name = file_name + f"-{self.reference_link}"
                file_name = file_name + ".pdf"

                file_doc = frappe.get_doc(
                    {
                        "doctype": "File",
                        "attached_to_doctype": self.doctype,
                        "attached_to_name": self.name,
                        "file_name": file_name,
                        "is_private": 0,
                        "content": document_pdf,
                    }
                ).insert()

                documents.append(
                    {
                        "id": document_id,
                        "file": document_pdf,
                        "name": template_context.get("document"),
                        "extension": "pdf",
                        "recipients": template_context.get("recipients")[0],
                    }
                )

                self.append("documents", {"document": file_doc.name, "id": document_id})
            else:
                template_data.append(template_context.get("template_data"))

        send_envelope(self, documents, template_data)
        self.save()

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
