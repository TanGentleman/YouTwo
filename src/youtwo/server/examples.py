ENTITY_1 = {
    "name": "Tan",
    "entityType": "person",
    "observations": ["Tan often craves cheese"],
    "journalIds": []
}

ENTITY_2 = {
    "name": "Kiren",
    "entityType": "person",
    "observations": ["Kiren is beautiful"],
    "journalIds": []
}

ENTITY_3 = {
    "name": "Cheese",
    "entityType": "food",
    "observations": ["Cheese is delicious"],
    "journalIds": []
}

RELATION_1 = {
    "to": ENTITY_1["name"],
    "from": ENTITY_2["name"],
    "relationType": "loves"
}

RELATION_2 = {
    "to": ENTITY_2["name"],
    "from": ENTITY_1["name"],
    "relationType": "loves"
}

RELATION_3 = {
    "to": ENTITY_1["name"],
    "from": ENTITY_3["name"],
    "relationType": "likes"
}
