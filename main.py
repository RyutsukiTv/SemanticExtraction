import json

import requests
import re
from jdm_api import JDMCache
from node import Node, SuperNode

rules_file = "rules_for_GN.json"
##Mise en etape
def multi_phrase_en_array(text):
    if not isinstance(text, str):
        raise ValueError("L'entrée doit être une chaîne de caractères.")

    # Utiliser une regex pour découper le texte en phrases
    phrases = re.split(r"[.!?,']", text)

    return phrases

def phrase_en_array(phrase):
    # Découper la phrase en mots
    mots = phrase.split()
    return mots


## Obtenir le nom des Relations
def get_relation_name(id):
    # Effectuer la requête pour obtenir les types de relations
    response = requests.get("https://jdm-api.demo.lirmm.fr/v0/relations_types")

    # Vérifier si la requête est réussie
    if response.status_code == 200:
        # Convertir la réponse en JSON (liste de dictionnaires)
        relations = response.json()

        # Parcourir les relations et chercher celle correspondant à l'id
        for relation in relations:
            if relation["id"] == id:
                return relation["name"]

        # Si l'id n'est pas trouvé, renvoyer None
        return None

    else:
        # En cas d'erreur dans la requête, lever une exception
        response.raise_for_status()



## Trouver la categorie pour Determinant les plus generique
def trouver_categorie(mots_categorie, mot):
    # Liste des catégories des mots
    categories = {
        "Det:": [
            "le", "la", "l'", "les",
            "un", "une", "des",
            "mon", "ma", "mes",
            "ton", "ta", "tes",
            "son", "sa", "ses",
            "notre", "nos",
            "votre", "vos",
            "leur", "leurs"
        ]
    }

    # Convertir le mot en minuscules
    mot = mot.lower()

    # Vérifier si mots_categorie est valide
    if mots_categorie is None:
        return None

    # Parcours de chaque catégorie
    for categorie in mots_categorie:
        categorie = categorie.strip("'")  # Enlever les guillemets et convertir en minuscule
        # Vérifier si le mot appartient à la catégorie
        if categorie in categories:
            if mot in categories[categorie]:
                cat = []
                cat.append(categorie)
                return cat
    return None

## Obtention de l ID du mot
def getIDWord(mot):
    try:
        # Récupérer les données
        data = jdm_cache.fetch_relations(mot, entrant=True, relation="")

        # Vérifier si les données sont vides ou si la clé "r" est absente
        if not data or "r" not in data:
            #print(f"Aucune relation trouvée pour le mot '{mot}'.")
            return None

        # Récupérer le premier noeud
        for rel_id, rel_info in data["r"].items():
            node1 = rel_info["node1"]

        return node1  # Retourner le node1 trouvé

    except Exception as e:
        # Gestion d'erreur en cas de problème
        #print(f"Erreur lors de la récupération de l'ID pour le mot '{mot}': {e}")
        return None

def definir_nombre_chaine(matched_string):
    mots = matched_string.split("_")  # Divise la chaîne en une liste de mots
    total_mots = len(mots)

    if total_mots == 0:
        return "indéterminé"  # Gestion des cas vides

    # Compte les mots qui se terminent par 's' ou 'x'
    pluriels = sum(1 for mot in mots if mot.lower().endswith(("s", "x")) and mot.lower() != "s")

    # Détermine si la majorité des mots sont au pluriel
    if pluriels > total_mots / 2:
        return "pluriel"
    return "singulier"


## COnvertion de la phrase en plusieur Nodes
def phrase_to_node(array):
    nodes = []

    # Inverser l'ordre des mots
    array.reverse()

    # Calculer la longueur de l'array
    length = len(array)

    # Créer un Node pour chaque mot dans l'ordre inversé
    for i, word in enumerate(array):
        node = Node(
            version=1,
            mot=word,
            idmot=getIDWord(word),
            position=length - i,  # La position commence à la longueur de l'array et décrémente
            lemm=word.lower(),  # Utiliser le mot en minuscules comme forme lemmatisée
            idlemm=None,
            nombre=verifie_nombre(word),
            relation_id=[-1],  # Laissez vide ou ajustez selon votre logique
            relation=["r_succ"],  # Par défaut, on peut dire que c'est un "mot"
            wordType= None
        )
        nodes.append(node)

    for i in range(len(nodes) - 1):
        data = JDMCache.getData(jdm_cache, nodes[i].lemm,"_END", "r_lemma")
        result = {key: value for key, value in data['r'].items() if
                  value['node1'] == nodes[i].idmot and value['type'] == "19"}
        for key, value in result.items():
            response = requests.get(f"https://jdm-api.demo.lirmm.fr/v0/node_by_id/{value['node2']}")

            # Vérifier si la requête a réussi
            if response.status_code == 200:
                data = response.json()

                # Extraire le nom du nœud, ou 'Unknown' si le nom est introuvable
                lemm = data.get('name', 'Unknown')
                lemmid = data.get('id', 'Unknown')
                nodes[i].lemm =  lemm
                nodes[i].idlemm =  int(lemmid)
            else:
                print(f"Failed to fetch category name for node2: {value['node2']}")


    for i in range(len(nodes) - 1):
        if i == 0:
            nodes[i].next_node_id = None  # Le premier node n'a pas de précédent
        else:
            nodes[i].next_node_id = nodes[i - 1].idmot  # Le next_node_id est l'idmot du node précédent

    nodes.reverse()

    for i in range(len(nodes) - 1):
        if i != len(nodes) - 1:
            data = JDMCache.getData(jdm_cache, nodes[i].lemm, nodes[i+1].lemm, "r_pos")
            result = {key: value for key, value in data['e'].items() if
                      value['type'] == '4' and int(value['w']) > 0 and value['name'].endswith(":'")}

            wordType = []
            for key, value in result.items():
                wordType.append(value['name'])
            nodes[i].wordType = wordType
        else:
            data = JDMCache.getData(jdm_cache, nodes[i].lemm, "_END", "r_pos")
            result = {key: value for key, value in data['e'].items() if
                      value['type'] == '4' and int(value['w']) > 0 and value['name'].endswith(":'")}

            wordType = []
            for key, value in result.items():
                wordType.append(value['name'])
            nodes[i].wordType = wordType


    for i in range(len(nodes) - 1):

        list_wordType = nodes[i].wordType
        resultat = trouver_categorie(list_wordType,nodes[i].lemm)
        if resultat != None:
            nodes[i].wordType = resultat

    for i in range(len(nodes) - 1):
        if i != len(nodes) - 1:
            ## Relation entre les Lemm
            data = JDMCache.getData(jdm_cache, nodes[i].lemm, nodes[i + 1].lemm, "r_pos")
            result = {key: value for key, value in data['r'].items() if
                      value['node1'] == str(nodes[i].idlemm) and value['node2'] == str(nodes[i + 1].idlemm) and value[
                          'type'] != "0" and value['type'] != "4"}
            #print("Lemm: " + str(nodes[i].idlemm) + " et " + str(nodes[i + 1].idlemm))
            #print("Lemm: " + nodes[i].lemm + " et " + nodes[i + 1].lemm)
            #print(result)
            #print( value['w'])
            types = [entry['type'] for entry in result.values()]

            relation = []
            for type in types:
                relation.append(get_relation_name(int(type)))

            nodes[i].relation = relation
            nodes[i].relation_id = types
            ##print(relation)

    for i in range(len(nodes) - 1):
        for type in nodes[i].wordType:
            #print(type)
            if type == "'Pro:'":
                for type2 in nodes[i + 1].wordType:
                    if type2 == "'Ver:'":
                        #print("r_agent")
                        r = "r_agent"
                        relation = []
                        relation.append(r)
                        nodes[i].relation = relation

                        nodes[i+1].wordType = [t for t in nodes[i+1].wordType if t == "'Ver:'"]

        for i in range(len(nodes)):
            # Vérifier si wordType existe et est une liste avant d'itérer dessus
            if nodes[i].wordType is not None:
                for type in nodes[i].wordType:
                    # Vérifier si le type correspond à "Ver:" ou "GV:"
                    if type == "'Ver:'" or type == "'GV:'":
                        # Vérifier le wordType du nœud suivant (nodes[i + 1])
                        if i + 1 < len(nodes) and nodes[i + 1].wordType is not None:
                            for type2 in nodes[i + 1].wordType:
                                if type2 == "'Adv:'":
                                    r = "r_patient"
                                    relation = []
                                    relation.append(r)
                                    nodes[i].relation = relation

                                    nodes[i + 1].wordType = [t for t in nodes[i + 1].wordType if t == "'Ver:'"]
                        else:
                            # Gérer le cas où wordType de nodes[i + 1] est None ou index out of range
                            print(f"Warning: 'wordType' is None or out of range for node at index {i + 1}.")
            else:
                # Gérer le cas où wordType de nodes[i] est None
                print(f"Warning: 'wordType' is None for node at index {i}.")

    return nodes



##Creation de GN
def read_rules(file_path):
    rules = []
    with open(file_path, 'r') as file:
        for line in file:
            if '=>' in line:
                pattern, result = line.strip().split('=>')
                rules.append((pattern.strip(), result.strip()))
    return rules

def verifie_nombre(mot):
    if mot == "dehors":
        return "singulier"
    if mot.lower().endswith("s") and mot.lower() != "s":
        return "pluriel"
    if mot.lower().endswith("x") and mot.lower() != "x":
        return "pluriel"
    return "singulier"


jdm_cache = JDMCache()


def test_sequence(nodes, rules):
    matching_nodes = []  # Liste pour stocker les nœuds qui respectent la règle

    for i in range(len(nodes)):
        for rule in rules:
            pattern = rule["pattern"]
            # On s'assure de respecter strictement le pattern
            selected_types = [word_type for word_type in nodes[i].wordType if word_type == pattern[0]]

            # Si le premier mot correspond bien à l'élément du pattern
            if selected_types:
                matched_nodes = [nodes[i]]
                for j in range(i + 1, len(nodes)):
                    # Si on a encore des éléments à vérifier dans le pattern
                    if len(matched_nodes) < len(pattern):
                        for word_type in nodes[j].wordType:
                            # Chaque nœud suivant doit correspondre exactement à l'élément suivant du pattern
                            if word_type == pattern[len(matched_nodes)]:
                                matched_nodes.append(nodes[j])
                                break
                    else:
                        break

                # Si la séquence respecte le pattern strictement
                if len(matched_nodes) == len(pattern):
                    # Remplacer le wordType des nœuds par ceux du pattern
                    for idx, node in enumerate(matched_nodes):
                        # Remplacer chaque wordType du nœud par celui du pattern
                        node.wordType = [pattern[idx].replace(":",
                                                              "")]  # On enlève le ":" pour appliquer le mot "Det", "Adj", "Nom" au lieu de "Det:", "Adj:", "Nom:"
                    matching_nodes.extend(matched_nodes)

                    # Concaténer les mots des nœuds validés sous forme de chaîne de caractères
                    matched_string = '_'.join([node.mot for node in matched_nodes])
                    return matching_nodes, matched_string  # Retourner les nœuds correspondants à la règle
            else:
                return None , None
    return None, None  # Retourner None si aucune règle n'est respectée


def determine_genre(phrase):
    """
    Détermine le genre (masculin ou féminin) d'une chaîne de caractères en fonction des mots-clés.

    :param phrase: La chaîne de caractères à analyser.
    :return: "masculin", "féminin", ou None si aucun genre n'est trouvé.
    """
    # Mots-clés pour les genres
    mots_masculins = {'le', 'un','Un', 'mon', 'ton', 'son', 'ce', 'aucun','du'}
    mots_feminins = {'la', 'une', 'ma', 'ta', 'sa', 'cette', 'aucune'}

    # Découper la phrase en mots
    mots = phrase.split('_')

    # Vérifier les mots pour trouver le genre
    for mot in mots:
        if mot in mots_masculins:
            return "masculin"
        elif mot in mots_feminins:
            return "féminin"

    # Aucun genre trouvé
    return None


def main(SuperNodePrecedant =None):
    # Exemple des règles
    try:
        rules_file = "rules_for_GN.json"  # Définir le chemin de ton fichier JSON
        with open(rules_file, "r", encoding="utf-8") as file:
            rules = json.load(file)  # Charger le contenu du fichier JSON en tant que liste de dictionnaires
    except FileNotFoundError:
        print(f"Erreur : Le fichier {rules_file} est introuvable.")
        rules = []
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier {rules_file} contient un JSON invalide.")
        rules = []

    # Vérifier si des règles ont été chargées
    if not rules:
        print("Aucune règle n'a été chargée.")
        return

    copy_nodes = nodes.copy()

    # Liste des SuperNodes
    superNodes = []
    nb_de_nodes = len(copy_nodes)
    pos = 0
    while nb_de_nodes > 0:
        # Tester la séquence de nœuds
        matching_nodes, matched_string = test_sequence(copy_nodes, rules)

        if matching_nodes:
            # Si une règle a été trouvée, on crée un SuperNode
            last_relation = None
            for node in matching_nodes:
                if node.relation:  # Vérifie si la liste n'est pas vide
                    last_relation = node.relation[0]
                copy_nodes.remove(node)
                nb_de_nodes -= 1
            # Ajouter un SuperNode à la liste superNodes
            super_node = SuperNode(version=2, position=pos,nombre=definir_nombre_chaine(matched_string), id=getIDWord(matched_string), groupeDeMot=[matched_string], lemm=[matched_string], next_node_id=None, relation=[last_relation],genre=determine_genre(matched_string))
            superNodes.append(super_node)
            pos += 1
        else:
            # Si aucun pattern ne correspond, ajouter un SuperNode pour le nœud courant
            node = copy_nodes.pop(0)
            super_node = SuperNode(version=2, position=pos,nombre=node.nombre, id=getIDWord(node.mot), groupeDeMot=[node.mot], lemm=node.lemm, next_node_id=None, relation=node.relation,genre=determine_genre(node.mot))
            superNodes.append(super_node)
            nb_de_nodes -= 1
            pos += 1


    # Relier les SuperNodes
    for i in range(len(superNodes)):
        superNodes[i].next_node_id = superNodes[i+1].id if i != len(superNodes)-1 else None
        # PAS DE RELATION TROUVER

        if superNodes[i].relation == []:
            ## Relation entre les groupeDeMot
            premier_mot = ""
            if (i+1) < len(superNodes):
                premier_mot = superNodes[i + 1].lemm
            node1 = superNodes[i].lemm
            node2 = ""
            if (i+1) < len(superNodes):
                node2 = superNodes[i + 1].lemm

            # Vérifier si node2 est une liste
            if isinstance(node2, list):
                # Convertir la liste en chaîne en prenant le premier élément ou en joignant les éléments
                node2 = "_".join(node2)  # Joindre les éléments avec un underscore (_)

            # Liste des mots-clés
            mots_cles = ['du', 'de', 'dans', 'le', 'la', 'les', 'ses', 'sa', 'son', 'sont', 'leur', 'leurs', 'mon',
                         'ma','qui' ]

            # Créer un pattern regex pour correspondre aux mots-clés suivis d'un mot
            pattern = rf"\b({'|'.join(mots_cles)})_([a-zA-Z]+)"

            # Chercher une correspondance
            match = re.search(pattern, node2)

            if match:
                # Extraire le mot après le mot-clé
                premier_mot = match.group(2)
                #print(premier_mot)
                # print(f"Premier mot trouvé : {premier_mot}")
            apiCall = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{node1}/to/{premier_mot}"
            #print(apiCall)
            response = requests.get(apiCall)
            # Vérifier que la requête a réussi
            if response.status_code == 200:
                # Extraire le JSON de la réponse
                data = response.json()

                # Vérifier que les relations sont présentes
                if "relations" in data:
                    relations = data["relations"]

                    # Trouver la relation avec le poids le plus grand
                    # Trouver la relation avec le poids le plus grand
                    if relations:  # Vérifier que la liste n'est pas vide
                        relation_max = max(relations, key=lambda rel: rel["w"])
                        relationName = get_relation_name(relation_max['type'])

                        if not isinstance(superNodes[i].relation, list):
                            superNodes[i].relation = []  # Réinitialiser à une liste vide si ce n'est pas une liste

                        superNodes[i].relation.append(relationName)

                        #print(f"Type de la relation avec le plus grand poids : {relationName} for {superNodes[i].groupeDeMot}")
                    else:
                        print("Aucune relation trouvée.")

                else:
                    print("Le format de la réponse ne contient pas de clé 'relations'.")
            #else:
                #print(f"Erreur lors de la requête : {response.status_code}")

            # superNodes[i].relation_id = types
            # print(relation)
        # Afficher les SuperNodes
    for i in range(len(superNodes)):
        if superNodes[i].groupeDeMot == ['elle']:
            superNodes[i].genre = "feminin"
            superNodes[i].nombre = "singulier"
            #print("Feminin " + " ".join(superNodes[i].groupeDeMot))
        if superNodes[i].groupeDeMot == ['il']:
            superNodes[i].genre = "masculin"
            superNodes[i].nombre = "singulier"
            #print("masculin " + " ".join(superNodes[i].groupeDeMot))
        if superNodes[i].groupeDeMot == ['elles']:
            superNodes[i].genre = "feminin"
            superNodes[i].nombre = "pluriel"
            #print("Feminin " + " ".join(superNodes[i].groupeDeMot))
        if superNodes[i].groupeDeMot == ['ils']:
            superNodes[i].genre ="masculin"
            superNodes[i].nombre = "pluriel"
            #print("masculin " + " ".join(superNodes[i].groupeDeMot))


    if SuperNodePrecedant != None:
        for i in range(len(superNodes)): ## super node actuelle
            #print(superNodes[i].groupeDeMot)
            if superNodes[i].groupeDeMot == ['elle'] or superNodes[i].groupeDeMot == ['il'] or superNodes[i].groupeDeMot == ['elles'] or superNodes[i].groupeDeMot == ['ils'] and superNodes[i].groupeDeMot == ['Elle'] or superNodes[i].groupeDeMot == ['Il'] or superNodes[i].groupeDeMot == ['Elles'] or superNodes[i].groupeDeMot == ['Ils']:
                for j in range(len(SuperNodePrecedant)):
                    if SuperNodePrecedant[j].genre == superNodes[i].genre and SuperNodePrecedant[j].nombre == superNodes[i].nombre:
                       # print("OUI")
                        #print(str(superNodes[i].groupeDeMot) + " ref to " + str(SuperNodePrecedant[i].groupeDeMot))
                        superNodes[i].ref_to_GN = SuperNodePrecedant[i].groupeDeMot
                    print("Pas de Reference trouvé")









    print("Apres traitement grammaticale")
    for node in nodes:
        if len(node.wordType) > 1:  # Vérifie si le type de mot contient plus d'un élément
            # Liste des catégories à supprimer
            categories_a_enlever = ['Nom:', 'Adj:']
            # Filtrer et mettre à jour node.wordType
            node.wordType = [type_mot for type_mot in node.wordType if type_mot not in categories_a_enlever]
        print(node)
    print("Groupe et relation grammaticale")
    for super_node in superNodes:
        print(super_node)



    # Afficher les SuperNodes
    print("Après traitement grammatical")
    for super_node in superNodes:
        print(super_node)



    return superNodes

if __name__ == "__main__":
    # Exemple de phrase
    phrase = "Le petit chat boit du lait."

    phrase = phrase.lower()
    resultat = multi_phrase_en_array(phrase)
    superNode = None
    for i, phrase in enumerate(resultat, start=1):
        if phrase == "":
            continue
        print(f"Phrase {i} : {phrase}")
        # Appel de la fonction pour transformer la phrase en liste
        array = phrase_en_array(phrase)

        # Conversion de la liste en Node, en partant du dernier mot vers le premier
        nodes = phrase_to_node(array)

        for node in nodes:
            node.clean_word_type()
        # Affichage du résultat
        #for node in nodes:
        #    print(node)

        if superNode == None:
            #print("pas de superNode")
            superNode = main()
        else:
            #print("superNode")
            superNode = main(superNode)
