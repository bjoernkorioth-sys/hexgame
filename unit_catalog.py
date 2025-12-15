UNIT_CATALOG = {
    "captain": {
        "cost": 100,
        "icon": "icons/captain.png",
        "stats": {
            "move_range": 3,
            "hp": 2,
            "save": 3,
            "morale": 10,
            "melee": {"attack": 2, "hit": 3, "damage": 2, "range": 1},
            "ranged": {"attack": 0, "hit": 0, "damage": 0, "range": 0},
            "action_points": 3,
        }
    },

    "soldier": {
        "cost": 50,
        "icon": "icons/soldier.png",
        "stats": {
            "move_range": 3,
            "hp": 1,
            "save": 2,
            "morale": 8,
            "melee": {"attack": 2, "hit": 3, "damage": 2, "range": 1},
            "action_points": 2,
        }
    },

    "marksman": {
        "cost": 75,
        "icon": "icons/marksman.png",
        "stats": {
            "move_range": 3,
            "hp": 1,
            "save": 1,
            "morale": 8,
            "melee": {"attack": 1, "hit": 1, "damage": 1, "range": 1},
            "ranged": {"attack": 1, "hit": 3, "damage": 1, "range": 10},
            "action_points": 2,
        }
    }
}
