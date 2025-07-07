import frappe

from crm_docusign_integration.config.config import ROLES


def after_install():
    add_docusign_roles()


def add_docusign_roles():
    for role in ROLES:
        if not frappe.db.exists("Role", {"role_name": role}):
            create_role(role)
    frappe.db.commit()


def create_role(role_name):
    role = frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
        }
    )
    role.insert(ignore_permissions=True)
    return role.name
