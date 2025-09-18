import requests
from crm_docusign_integration.docusign.integration.auth import get_authorization_token


def make_post_req(url, data=None, json=None):
    headers = prepare_headers()

    return requests.post(url, data=data, json=json, headers=headers)


def make_get_req(url, params=None):
    headers = prepare_headers()

    return requests.get(url, params=params, headers=headers)


def prepare_headers():
    return {
        "Authorization": get_authorization_token(),
        "Content-Type": "application/json",
    }
