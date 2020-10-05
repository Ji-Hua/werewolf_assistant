import pytest

from app.domain.models import GameTemplate


def test_template_could_create_correctly():
    name = "预女猎白混"
    characters = {
        "预言家": 1,
        "女巫": 1,
        "猎人": 1,
        "白痴": 1,
        "狼人": 4,
        "村民": 3,
        "混血儿": 1
    }
    template = GameTemplate(name=name, characters=characters)
    assert template.characters == characters and template.name == name


def test_template_will_raise_if_characters_are_wrong():
    name = "预女猎白混"
    characters = {
        "预言家": 1,
        "女巫": 1,
        "猎人": 1,
        "白痴": 1,
        "狼人": 4,
        "村民": 3,
        "混血儿": "some number"
    }
    with pytest.raises(TypeError):
        template = GameTemplate(name=name, characters=characters)


def test_templates_with_the_same_characters_equal_to_each_other():
    characters = {
        "预言家": 1,
        "女巫": 1,
        "猎人": 1,
        "白痴": 1,
        "狼人": 4,
        "村民": 3,
        "混血儿": 1
    }
    t1 = GameTemplate("something", characters)
    t2 = GameTemplate("something else", characters)
    assert t1 == t2


def test_templates_with_different_characters_are_different():
    characters1 = {"预言家": 1, "女巫": 1, "猎人": 1, "白痴": 1, 
        "狼人": 4, "村民": 3, "混血儿": 1}
    characters2 = {"预言家": 1, "女巫": 1, "猎人": 1, "白痴": 1, 
        "狼人": 4, "村民": 4}
    t1 = GameTemplate('some name', characters=characters1)
    t2 = GameTemplate('some name', characters=characters2)
    assert t1 != t2


def test_template_raises_value_error_if_player_number_not_match():
    # 13 characters
    characters = {"预言家": 1, "女巫": 1, "猎人": 1, "白痴": 1, 
        "狼人": 4, "村民": 4, "混血儿": 1}
    with pytest.raises(ValueError):
        GameTemplate('name', characters)


def test_template_could_shuffle_characters_correctly():
    name = "预女猎白混"
    characters = {
        "预言家": 1,
        "女巫": 1,
        "猎人": 1,
        "白痴": 1,
        "狼人": 4,
        "村民": 3,
        "混血儿": 1
    }

    template = GameTemplate(name=name, characters=characters)
    character_list = template.shuffle_characters()
    for key, value in characters.items():
        assert character_list.count(key) == value


def test_template_could_shuffle_characters_randomly():
    name = "预女猎白混"
    characters = {
        "预言家": 1,
        "女巫": 1,
        "猎人": 1,
        "白痴": 1,
        "狼人": 4,
        "村民": 3,
        "混血儿": 1
    }

    template = GameTemplate(name=name, characters=characters)
    character_list1 = template.shuffle_characters()
    character_list2 = template.shuffle_characters()
    assert character_list1 != character_list2