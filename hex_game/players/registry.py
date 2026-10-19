from hex_game.players.bot_minimax import MinimaxBot

AGENT_TYPES = (
    ("minimax", "Minimax (alfa-beta)"),
)

DIFFICULTIES = (
    ("easy", "Łatwy", 0.2),
    ("normal", "Średni", 1.0),
    ("hard", "Trudny", 3.0),
)

_FACTORIES = {
    "minimax": MinimaxBot,
}


def agent_labels():
    return [label for _, label in AGENT_TYPES]


def agent_key(position):
    return AGENT_TYPES[position][0]


def agent_label(key):
    return dict(AGENT_TYPES).get(key, key)


def difficulty_labels():
    return [label for _, label, _ in DIFFICULTIES]


def difficulty_key(position):
    return DIFFICULTIES[position][0]


def difficulty_label(key):
    for current, label, _ in DIFFICULTIES:
        if current == key:
            return label
    return key


def time_budget(key):
    for current, _, budget in DIFFICULTIES:
        if current == key:
            return budget
    return 1.0


def create_agent(kind, seat, difficulty="normal"):
    factory = _FACTORIES.get(kind)
    if factory is None:
        raise ValueError(f"unknown agent type: {kind}")
    return factory(seat, time_limit=time_budget(difficulty))
