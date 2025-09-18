import frappe
from base64 import b64decode
from crm_docusign_integration.docusign.integration import config


@frappe.whitelist(allow_guest=True)
def envelope_events_webhook():
    try:
        triggered_event = frappe.form_dict.get("event")
        envelope_data = frappe.form_dict.get("data", {})
        envelope_id = envelope_data.get("envelopeId")
        sys_envelopes = frappe.db.get_all(
            "Envelope", "name", {"envelope_id": envelope_id}, limit=1
        )

        if len(sys_envelopes):
            envelope_doc = frappe.get_doc("Envelope", sys_envelopes[0]["name"])
            new_envelope_status = (
                config.ENVELOPE_EVENT_STATUS_MAP.get(triggered_event) or ""
            )
            is_completed = triggered_event == config.ENVELOPE_COMPLETED_EVENT

            if new_envelope_status:
                envelope_doc.update(
                    {
                        "envelope_status": new_envelope_status,
                        "signed": is_completed,
                    }
                )

            if is_completed:
                envelope_doc.docstatus = 1

                envelope_documents = envelope_data.get("envelopeSummary", {}).get(
                    "envelopeDocuments", []
                )

                attached_to_doctype = "Envelope"
                attached_to_name = envelope_doc.name
                if envelope_doc.get("reference_doctype"):
                    attached_to_doctype = envelope_doc.get("reference_doctype")
                    attached_to_name = envelope_doc.get("reference_link")

                for envp_doc in envelope_documents:
                    file_doc = frappe.get_doc(
                        {
                            "doctype": "File",
                            "file_name": f"{envp_doc.get('name')}-{envelope_doc.name}.pdf",
                            "is_private": 0,
                            "content": b64decode(envp_doc.get("PDFBytes")),
                        }
                    )
                    if envp_doc.get("type") == "summary":
                        # Its an certificate doc
                        file_doc = file_doc.update(
                            {
                                "attached_to_field": "certificate",
                                "attached_to_doctype": envelope_doc.doctype,
                                "attached_to_name": envelope_doc.name,
                            }
                        ).insert(ignore_permissions=True)

                        envelope_doc.certificate = file_doc.name
                    else:
                        file_doc = file_doc.update(
                            {
                                "attached_to_doctype": attached_to_doctype,
                                "attached_to_name": attached_to_name,
                            }
                        ).insert(ignore_permissions=True)

                        for document in envelope_doc.get("documents", default=[]):
                            if document.get("id") == envp_doc.get("documentId"):
                                document.update({"signed_document": file_doc.name})
            envelope_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error("Error occured in envelope_events_webhook", e)
        frappe.log_error("DocuSign webhook event data", frappe.form_dict)
