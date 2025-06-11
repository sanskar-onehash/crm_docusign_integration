# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe

from jinja2 import TemplateSyntaxError
from frappe.model.document import Document
from frappe.utils import md_to_html
from frappe.utils.safe_exec import safe_exec
from frappe.utils.jinja import render_template
from frappe.utils.pdf import get_pdf


class DocumentTemplate(Document):

    def get_document_context(self, doctype=None, docname=None):
        if not hasattr(self, "_context"):
            self._context = frappe._dict()
            self._context["doctype"] = doctype
            self._context["docname"] = docname

            if self.context_script:
                _locals = dict(context=self._context)
                safe_exec(
                    self.context_script,
                    None,
                    _locals,
                    script_filename=f"document {self.name}-{doctype or ''}-{docname or ''}",
                )
                self._context.update(_locals["context"])
            self._context.update(
                {
                    "style": self.css if self.insert_style and self.css else "",
                    "script": "",
                    "header": "",
                    "text_align": "",
                }
            )
        return self._context

    def generate_markup(self, doctype=None, docname=None):
        self.get_document_context(doctype, docname)

        self.render_dynamic(self._get_html_markup(), self._context)
        return self._context.get("main_section")

    def generate_pdf(self, doctype=None, docname=None):
        self.generate_markup(doctype, docname)
        return get_pdf(self._context.get("main_section"))

    def _get_html_markup(self):
        if self.content_type == "Markdown":
            return md_to_html(self.markdown)
        if self.content_type == "Rich Text":
            return self.rich_text or ""
        return self.html or ""

    def render_dynamic(self, content, context):
        if "{{" in content:
            frappe.flags.web_block_scripts = {}
            frappe.flags.web_block_styles = {}
            try:
                context["main_section"] = render_template(content, context)
                if "<!-- static -->" not in context.main_section:
                    context["no_cache"] = 1
            except TemplateSyntaxError:
                raise
            finally:
                frappe.flags.web_block_scripts = {}
                frappe.flags.web_block_styles = {}
