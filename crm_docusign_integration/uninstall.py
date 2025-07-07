import frappe

from crm_docusign_integration.config.config import ROLES


def after_uninstall():
    remove_docusign_roles()


def remove_docusign_roles():
    for role in ROLES:
        if frappe.db.exists("Role", {"role_name": role}):
            delete_role(role)
    frappe.db.commit()


def delete_role(role_name):
    frappe.get_doc(
        "Role",
        {
            "role_name": role_name,
        },
    ).delete()
