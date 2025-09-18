def parse_templates(templates_res):
    templates = []

    for template in templates_res["envelopeTemplates"] or []:
        templates.append(
            {"template_id": template["templateId"], "template_name": template["name"]}
        )

    return templates
