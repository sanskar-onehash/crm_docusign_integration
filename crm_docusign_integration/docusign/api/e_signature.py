import json
import frappe
from frappe.utils import base64
from crm_docusign_integration.docusign.api import make_post_req


def send_envelop(envelop_doc, documents):
    docusign_settings = frappe.get_doc("DocuSign Integration", "DocuSign Integration")

    envelop_data = {
        "status": "sent",
        "emailSubject": envelop_doc.subject,
        "documents": [],
        "recipients": {"signers": []},
    }

    for idx, document in enumerate(documents):
        document_id = str(idx + 1)
        envelop_data["documents"].append(
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

            envelop_data["recipients"]["signers"].append(signer)
            recipient_id = recipient_id + 1

    res = make_post_req(
        f"{docusign_settings.get('api_base_uri')}/restapi/v2.1/accounts/{docusign_settings.get('api_account_id')}/envelopes",
        json.dumps(envelop_data),
    )
    res_data = json.loads(res.text or "{}")

    if res_data.get("envelopeId"):
        envelop_doc.update({"envelop_id": res_data.get("envelopeId")})
        envelop_doc.save()
    else:
        frappe.log_error(
            "Error sending envelop", {"status": res.status_code, "data": res.text}
        )
        frappe.throw(f"Error occured while sending the envelope: {res.text}")
