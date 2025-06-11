import requests
from crm_docusign_integration.docusign.api.auth import get_authorization_token


def make_post_req(url, data):
    headers = {
        "Authorization": get_authorization_token(),
        "Content-Type": "application/json",
    }

    return requests.post(url, data, headers=headers)


def make_get_req(url):
    headers = {
        "Authorization": get_authorization_token(),
        "Content-Type": "application/json",
    }

    return requests.get(url, headers=headers)
