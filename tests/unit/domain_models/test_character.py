from app.domain import Character, Skill


def test_character_has_name_and_camp():
    character = Character(name='村民', camp=['民'])
    assert character.name == '村民' and '民' in character.camp


def test_character_default_skills_is_empty_list():
    character = Character(name='村民', camp=['民'])
    assert character.skills == []


def test_character_skills_are_correct():
    intro_text = "夜间，你和其他狼人一起睁眼，可以「刀杀」一名存活的玩家。"
    skill = Skill(name='猎杀', introduction=intro_text)
    character = Character(name='村民', camp=['民'], skills=[skill])
    assert skill in character.skills
