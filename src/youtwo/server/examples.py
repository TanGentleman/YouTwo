ENTITY_1 = {
    "name": "Tan",
    "entityType": "person",
    "observations": ["Tan often craves cheese"],
    "journalIds": [],
}

ENTITY_2 = {
    "name": "Kiren",
    "entityType": "person",
    "observations": ["Kiren is beautiful"],
    "journalIds": [],
}

ENTITY_3 = {
    "name": "Cheese",
    "entityType": "food",
    "observations": ["Cheese is delicious"],
    "journalIds": [],
}

RELATION_1 = {
    "target": ENTITY_1["name"],
    "source": ENTITY_2["name"],
    "relationType": "loves",
}

RELATION_2 = {
    "target": ENTITY_2["name"],
    "source": ENTITY_1["name"],
    "relationType": "loves",
}

RELATION_3 = {
    "target": ENTITY_1["name"],
    "source": ENTITY_3["name"],
    "relationType": "likes",
}
