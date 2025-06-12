import json
import frappe
from frappe.utils import base64
from crm_docusign_integration.docusign.api import make_post_req


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
                "recipient-declined",
                "recipient-delivered",
                "recipient-completed",
            ],
            "eventData": {"version": "restv2.1"},
            "includeCertificateOfCompletion": "true",
            "includeCertificateWithSoap": "true",
            "includeDocuments": "true",
            "includeEnvelopeVoidReason": "true",
            "includeHMAC": "true",
            "url": f"https://{frappe.local.site}/api/method/crm_docusign_integration.docusign.api.e_signature.envelope_events_webhook",
        },
    }

    # Add documents and recipients
    for idx, document in enumerate(documents):
        document_id = str(idx + 1)
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
