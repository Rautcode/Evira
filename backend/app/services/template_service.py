import os
import re
import json
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))

# Template ids map directly to filenames, so restrict them to a safe charset
# to prevent path traversal (e.g. "../../etc/passwd").
_VALID_TEMPLATE_ID = re.compile(r'^[A-Za-z0-9_-]{1,128}$')


class TemplateService:
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(enabled_extensions=("html", "htm", "xml")),
        )

    def _path_for(self, template_id: str) -> str:
        """Validate a template id and return its on-disk JSON path."""
        if not template_id or not _VALID_TEMPLATE_ID.match(template_id):
            raise ValueError("Invalid template id")
        return os.path.join(self.templates_dir, f"{template_id}.json")

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
        path = self._path_for(template_id)
        if not os.path.exists(path):
            raise FileNotFoundError("Template not found")
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_template(self, template_id: str, data: Dict[str, Any]):
        path = self._path_for(template_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return True

    def edit_template(self, template_id: str, updates: Dict[str, Any]):
        template = self.load_template(template_id)
        template.update(updates)
        self.save_template(template_id, template)
        return True

    def delete_template(self, template_id: str) -> bool:
        path = self._path_for(template_id)
        if not os.path.exists(path):
            raise FileNotFoundError("Template not found")
        os.remove(path)
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
