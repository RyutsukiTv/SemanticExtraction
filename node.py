class Node:
    def __init__(self, version: int, wordType: list[str], mot: str, idmot: int, idlemm: int, position: int, lemm: str,
                 nombre: str, next_node_id: int = None, relation_id: list[int] = None, relation: list[str] = None):
        self.version = version
        self.mot = mot
        self.idmot = idmot
        self.position = position
        self.lemm = lemm
        self.nombre = nombre
        self.next_node_id = next_node_id
        self.relation_id = relation_id
        self.relation = relation if isinstance(relation, list) else []
        self.wordType = wordType
        self.idlemm = idlemm
    def __repr__(self):
        return f"Node(version={self.version}, wordType={self.wordType}, mot={self.mot}, idmot={self.idmot}, position={self.position}, lemm={self.lemm}, idlemm={self.idlemm}, nombre={self.nombre}, next_node_id={self.next_node_id}, relation_id={self.relation_id}, relation={self.relation})"

    def get_next_node(self, nodes):
        return next((node for node in nodes if node.idmot == self.next_node_id), None)

    def clean_word_type(self):
        """
        Supprime les guillemets simples et doubles dans la liste wordType.
        Si wordType est None, l'initialiser comme une liste vide.
        """
        if self.wordType is None:
            self.wordType = []  # Initialiser comme une liste vide si None

        self.wordType = [word.strip('"\'') for word in self.wordType]


class SuperNode:
    def __init__(self, version: int,lemm:str,nombre:str,genre: str, id: int,position: int, groupeDeMot: list[str], next_node_id: int = None,
                 relation: list[str] = None):
        self.version = version
        self.groupeDeMot = groupeDeMot
        self.id = id
        self.position=position
        self.nombre = nombre
        self.next_node_id = next_node_id
        self.lemm = lemm
        self.ref_to_GN = None
        self.genre = genre
        self.relation = relation if isinstance(relation, list) else []

    def __repr__(self):
        return f"SuperNode(position={self.position},version={self.version}, genre={self.genre},id={self.id}, nombre={self.nombre},groupeDeMot={self.groupeDeMot},lemm={self.lemm},ref_To={self.ref_to_GN}, next_node_id={self.next_node_id}, relation={self.relation})"
