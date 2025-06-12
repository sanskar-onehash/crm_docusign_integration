import json
import frappe
from frappe.utils import base64
from crm_docusign_integration.docusign.api import make_post_req
from crm_docusign_integration.docusign.api.config import (
    ENVELOPE_EVENT_STATUS_MAP,
    ENVELOPE_SIGNED_EVENT,
)


def send_envelope(envelope_doc, documents):
    envelope_data = prepare_envelope(envelope_doc, documents)
    docusign_settings = frappe.get_doc("DocuSign Integration", "DocuSign Integration")

    res = make_post_req(
        f"{docusign_settings.get('api_base_uri')}/restapi/v2.1/accounts/{docusign_settings.get('api_account_id')}/envelopes",
        json.dumps(envelope_data),
    )
    res_data = json.loads(res.text or "{}")

    if res_data.get("envelopeId"):
        envelope_doc.update({"envelope_id": res_data.get("envelopeId")})
        envelope_doc.save()
    else:
        frappe.log_error(
            "Error sending envelope", {"status": res.status_code, "data": res.text}
        )
        frappe.throw(f"Error occured while sending the envelope: {res.text}")


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
            new_envelope_status = ENVELOPE_EVENT_STATUS_MAP.get(triggered_event, "")
            is_signed = triggered_event == ENVELOPE_SIGNED_EVENT

            if new_envelope_status:
                envelope_doc.update(
                    {
                        "envelope_status": new_envelope_status,
                        "signed": is_signed,
                    }
                )

            if is_signed:
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
                            "content": base64.b64decode(envp_doc.get("PDFBytes")),
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

                        envelope_doc.update(
                            {"certificate": file_doc.name, "docstatus": 1}
                        )
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


def prepare_envelope(envelope_doc, documents):
    envelope_data = {
        "status": "sent",
        "emailSubject": envelope_doc.subject,
        "documents": [],
        "recipients": {"signers": []},
        "eventNotification": {
            "deliveryMode": "SIM",
            "events": [
                "envelope-delivered",
                "envelope-completed",
                "envelope-declined",
                "envelope-voided",
            ],
            "eventData": {"version": "restv2.1", "includeData": ["documents"]},
            "includeCertificateOfCompletion": "true",
            "includeCertificateWithSoap": "true",
            "includeDocuments": "true",
            "includeEnvelopeVoidReason": "true",
            "includeHMAC": "true",
            "url": f"https://{frappe.local.site}/api/method/crm_docusign_integration.docusign.api.e_signature.envelope_events_webhook",
        },
    }

    # Add documents and recipients
    for document in documents:
        document_id = document.get("id")
        envelope_data["documents"].append(
            {
                "name": document.get("name"),
                "documentId": document_id,
                "fileExtension": document.get("extension"),
                "documentBase64": base64.b64encode(document.get("file")).decode(
                    "ascii"
                ),
            }
        )

        doc_recipients = document.get("recipients")

        for signer in doc_recipients.get("signers"):
            recipient_id = 1

            if not signer.get("recipientId"):
                signer["recipientId"] = f"{document_id}.{recipient_id}"

            envelope_data["recipients"]["signers"].append(signer)
            recipient_id = recipient_id + 1

    return envelope_data
