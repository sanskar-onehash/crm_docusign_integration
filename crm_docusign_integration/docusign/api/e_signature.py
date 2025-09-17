import json
import frappe
from frappe.utils import base64
from crm_docusign_integration.docusign.api import (
    make_get_req,
    make_post_req,
    transformer,
)


def send_envelope(envelope_doc, documents, templates_data):
    envelope_data = prepare_envelope(envelope_doc, documents, templates_data)
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


def fetch_templates():
    docusign_settings = frappe.get_doc("DocuSign Integration", "DocuSign Integration")
    templates = []
    req_uri = f"{docusign_settings.get('api_base_uri')}/restapi/v2.1/accounts/{docusign_settings.get('api_account_id')}/templates"
    while True:
        res = make_get_req(req_uri)
        res.raise_for_status()
        data = res.json()

        templates.extend(transformer.parse_templates(data))

        if not data.get("nextUri"):
            break

        req_uri = data["nextUri"]

    return templates


def prepare_envelope(envelope_doc, documents, templates_data):
    if documents and templates_data:
        frappe.throw("Both Documents and Templates data is not supported")

    envelope_data = {
        "status": "sent",
        "emailSubject": envelope_doc.subject,
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
    for document in documents or []:
        if not envelope_data.get("documents"):
            envelope_data["documents"] = []

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

        for signer in doc_recipients.get("signers") or []:
            recipient_id = 1

            if not signer.get("recipientId"):
                signer["recipientId"] = f"{document_id}.{recipient_id}"

            if not envelope_data.get("recipients"):
                envelope_data["recipients"] = {"signers": []}

            envelope_data["recipients"]["signers"].append(signer)
            recipient_id = recipient_id + 1

    for idx, template_data in enumerate(templates_data):
        if not envelope_data.get("compositeTemplates"):
            envelope_data["compositeTemplates"] = []

        template_data.update({"compositeTemplateId": idx})
        envelope_data["compositeTemplates"].append(template_data)

    return envelope_data
