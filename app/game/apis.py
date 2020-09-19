from flask_restful import Resource

from app.models import GameTemplate


class Template(Resource):
    def get(self, template_name):
        template = GameTemplate.objects(name=template_name).first()
        return {'description': template.description}
