import os
import json
from typing import Dict, Any, List, Optional
import uuid

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))

class TemplateManager:
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

    def list_templates(self) -> List[Dict[str, Any]]:
        files = [f for f in os.listdir(self.templates_dir) if f.endswith('.json')]
        templates = []
        for f in files:
            with open(os.path.join(self.templates_dir, f), 'r') as file:
                data = json.load(file)
                templates.append({"id": f.replace('.json',''), **data})
        return templates

    def load_template(self, template_id: str) -> Dict[str, Any]:
        path = os.path.join(self.templates_dir, f"{template_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError("Template not found")
        with open(path, 'r') as f:
            return json.load(f)

    def save_template(self, data: Dict[str, Any], template_id: Optional[str] = None) -> str:
        if not template_id:
            template_id = str(uuid.uuid4())
        path = os.path.join(self.templates_dir, f"{template_id}.json")
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return template_id

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        template = self.load_template(template_id)
        template.update(updates)
        self.save_template(template, template_id)
        return True

    def delete_template(self, template_id: str) -> bool:
        path = os.path.join(self.templates_dir, f"{template_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
