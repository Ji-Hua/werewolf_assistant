import json
import os

image_base = 'app/static/character_logo'

data_file = 'app/data/character_intro.json'


with open(data_file) as df:
    character_data = [*list(json.load(df).values())]

for group in character_data:
    for character_json in group:
        print(character_json['名字'])
        skills = []
        for skill_json in character_json['技能']:
            skill = Skill(name=skill_json['名称'], introduction=skill_json['说明'])
            skills.append(skill)
        character = Character(name=character_json['名字'], camp=character_json['归属'], skills=skills, note=character_json['注释'])
        with open(os.path.join(image_base, f"{character_json['名字']}.png"), 'rb') as img:
            character.image.put(img, content_type='image/png')
        
        try:
            character.save()
        except Exception as e:
            print(e)
            print(character.name)


with open('app/data/game_config.json') as df:
    templates = json.load(df)

for key, value in templates.items():
    template = GameTemplate(name=key, characters=value)
    template.save()