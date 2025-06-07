import frappe
import jwt
import json
import requests
from frappe import utils
from crm_docusign_integration.utils import format_pem_key

# Referece: https://developers.docusign.com/platform/auth/jwt-get-token/
AUTH_URI = "account-d.docusign.com"
SCOPES = "signature impersonation"


@frappe.whitelist()
def get_consent_url():
    docusign_settings = frappe.get_doc("DocuSign Integration", "DocuSign Integration")

    if not docusign_settings.get("enabled"):
        frappe.throw(
            "Your DocuSign Integration is not `enabled`. Please enable it and save the doc with required keys to continue."
        )

    base_url = f"https://{AUTH_URI}/oauth/auth"
    response_type = "code"
    scopes = utils.quote(SCOPES)
    client_id = docusign_settings.get("integration_key")
    redirect_uri = utils.quote(docusign_settings.get("redirect_uri", default=""))

    url = f"{base_url}?response_type={response_type}&scope={scopes}&client_id={client_id}&redirect_uri={redirect_uri}"

    return url


@frappe.whitelist(allow_guest=True)
def verify_consent(code):
    refresh_access_token(code)
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = utils.get_url_to_list("DocuSign Integration")


def get_authorization_token():
    docusign_settings = frappe.get_doc("DocuSign Integration", "DocuSign Integration")
    cur_time = utils.get_datetime()

    if not docusign_settings.get("is_verified") or not docusign_settings.get(
        "consent_code"
    ):
        frappe.throw("DocuSign credentials are not verified.")

    if (
        not docusign_settings.get("token_expiration")
        or docusign_settings.get("token_expiration") > cur_time
    ):
        refresh_access_token()
        docusign_settings.reload()

    return f"{docusign_settings.token_type} {docusign_settings.get_password('access_token')}"


def refresh_access_token(code=None):
    docusign_settings = frappe.get_doc("DocuSign Integration", "DocuSign Integration")

    if not docusign_settings.get("enabled"):
        frappe.throw("DocuSign Integration is not enabled.")

    if not code:
        code = docusign_settings.get_password("consent_code", False) or frappe.throw(
            "No consent code found. Please provide consent to verify integration."
        )

    private_key = format_pem_key(docusign_settings.get_password("private_key").strip())
    cur_time = utils.get_datetime()
    expiration_time = utils.add_to_date(cur_time, hours=1, as_datetime=True)

    jwt_headers = {
        "type": "JWT",
        "alg": "RS256",
    }
    jwt_body = {
        "iss": docusign_settings.get("integration_key"),
        "sub": docusign_settings.get("user_id"),
        "iat": utils.ceil(cur_time.timestamp()),
        "exp": utils.ceil(expiration_time.timestamp()),
        "aud": AUTH_URI,
        "scope": SCOPES,
    }
    jwt_key = jwt.encode(
        jwt_body,
        private_key,
        "RS256",
        jwt_headers,
    )

    url = f"https://{AUTH_URI}/oauth/token"
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_key,
    }
    res = requests.post(url, data)
    res_body = json.loads(res.text)

    if res_body.get("access_token"):
        docusign_settings.update(
            {
                "consent_code": code,
                "access_token": res_body.get("access_token"),
                "is_verified": True,
                "token_type": res_body.get("token_type"),
                "token_expiration": expiration_time,
            }
        )
        docusign_settings.save()
        frappe.db.commit()
    else:
        frappe.log_error(
            "Error Verifying DocuSign Consent",
            {"status_code": res.status_code, "msg": res.text},
        )
        frappe.throw(res.text)
