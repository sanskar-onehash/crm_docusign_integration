# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm_docusign_integration.docusign.api.e_signature import send_envelope


class Envelope(Document):

    def after_insert(self):
        documents = []

        for template in self.document_templates:
            template_doc = frappe.get_doc(
                "Document Template", template.document_template
            )
            document_pdf = template_doc.generate_pdf(
                self.reference_doctype, self.reference_link
            )
            template_context = template_doc.get_document_context(
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

            frappe.log_error("context", template_context)
            documents.append(
                {
                    "file": document_pdf,
                    "name": template_context.get("document"),
                    "extension": "pdf",
                    "recipients": template_context.get("recipients")[0],
                }
            )

            self.append("documents", {"document": file_doc.name})

        send_envelope(self, documents)
        self.save()
