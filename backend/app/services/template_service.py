import os
import json
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))

class TemplateService:
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    def list_templates(self):
        files = [f for f in os.listdir(self.templates_dir) if f.endswith('.json')]
        templates = []
        for f in files:
            with open(os.path.join(self.templates_dir, f), 'r') as file:
                data = json.load(file)
                templates.append({
                    "id": f.replace('.json',''),
                    "name": data.get("name", f),
                    "category": data.get("category", "General"),
                    "description": data.get("description", ""),
                    "previewUrl": data.get("previewUrl", ""),
                    "content": data.get("content", {})
                })
        return templates

    def load_template(self, template_id: str) -> Dict[str, Any]:
        path = os.path.join(self.templates_dir, f"{template_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError("Template not found")
        with open(path, 'r') as f:
            return json.load(f)

    def save_template(self, template_id: str, data: Dict[str, Any]):
        path = os.path.join(self.templates_dir, f"{template_id}.json")
        with open(path, 'w') as f:
            json.dump(data, f)
        return True

    def edit_template(self, template_id: str, updates: Dict[str, Any]):
        template = self.load_template(template_id)
        template.update(updates)
        self.save_template(template_id, template)
        return True

    def render_template(self, template_id: str, context: Dict[str, Any]) -> str:
        template_data = self.load_template(template_id)
        # Assume the main template content is in template_data['content']['body'] (or similar)
        # You may adjust this as per your template structure
        jinja_template_str = template_data['content'].get('body', '')
        jinja_template: Template = self.env.from_string(jinja_template_str)
        return jinja_template.render(**context)

    def preview_template(self, template_id: str, context: Dict[str, Any]) -> str:
        return self.render_template(template_id, context)
