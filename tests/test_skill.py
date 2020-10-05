from app.domain.models import Skill

def test_skill_has_name_and_intro():
    intro_text = "夜间，你和其他狼人一起睁眼，可以「刀杀」一名存活的玩家。"
    skill = Skill(name='猎杀', intro=intro_text)
    assert skill.name == '猎杀' and skill.intro == intro_text