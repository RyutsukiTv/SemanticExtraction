# jdm_api.py
import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import quote
import logging
import os
import json

class JDMCache:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_relations(self, mot, entrant, relation):
        """
        Récupère les relations via l'API JeuxDeMots et les stocke dans un cache local.
        """
        file_json_name = self.createJSON(mot, entrant, relation)
        data = self.getData(mot, entrant, relation)
        return data

    def getFromURL(self, mot, entrant, relation):
        """
        Récupère les données depuis l'API JeuxDeMots.
        """
        with requests.Session() as s:
            url = 'http://www.jeuxdemots.org/rezo-dump.php?'
            if entrant:
                payload = {
                    'gotermsubmit': 'Chercher',
                    'gotermrel': mot,
                    'relation': relation,
                    'relin': 'norelout'
                }
            else:
                payload = {
                    'gotermsubmit': 'Chercher',
                    'gotermrel': mot,
                    'relation': relation,
                    'relout': 'norelin'
                }

            r = s.get(url, params=payload)
            soup = bs(r.text, 'html.parser')
            prod = soup.find_all('code')
            while "MUTED_PLEASE_RESEND" in str(prod):
                r = s.get(url, params=payload)
                soup = bs(r.text, 'html.parser')
                prod = soup.find_all('code')
        return prod

    def convert(self, expression):
        """
        Convertit une expression en une liste de composants, gérant les apostrophes.
        """
        resultat = []
        tmp = ""
        cond = False
        for i in range(len(expression)):
            if i + 1 == len(expression):
                tmp += expression[i]
                resultat.append(tmp)
            else:
                if expression[i] == "'" and expression[i + 1] != ";":
                    cond = True
                elif expression[i] == "'" and expression[i + 1] == ";":
                    cond = False
                if cond:
                    tmp += expression[i]
                if not cond and expression[i] != ";":
                    tmp += expression[i]
                elif not cond and expression[i] == ";":
                    resultat.append(tmp)
                    tmp = ""
        return resultat

    def createTxt(self, mot, entrant, relation):
        """
        Crée un fichier TXT à partir des données récupérées de l'API.
        """
        prod = self.getFromURL(mot, entrant, relation)
        mot_clean = mot.replace(" ", "_").replace("'", "")
        if entrant:
            file_txt_name = f"{mot_clean}{relation}_e.txt"
        else:
            file_txt_name = f"{mot_clean}{relation}_s.txt"

        file_txt_path = os.path.join(self.cache_dir, file_txt_name)

        if not os.path.exists(file_txt_path) or os.path.getsize(file_txt_path) == 0:
            with open(file_txt_path, "w", encoding="utf-8") as file_txt:
                file_txt.write(str(prod))

        return file_txt_path

    def sanitize_filename(self, name):
        # Remplace les caractères invalides par un underscore "_"
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name

    def createTxt(self, mot, entrant, relation):
        """
        Crée un fichier TXT à partir des données récupérées de l'API.
        """
        prod = self.getFromURL(mot, entrant, relation)
        mot_clean = self.sanitize_filename(mot.replace(" ", "_").replace("'", ""))
        if entrant:
            file_txt_name = f"{mot_clean}{relation}_e.txt"
        else:
            file_txt_name = f"{mot_clean}{relation}_s.txt"

        file_txt_path = os.path.join(self.cache_dir, file_txt_name)

        if not os.path.exists(file_txt_path) or os.path.getsize(file_txt_path) == 0:
            with open(file_txt_path, "w", encoding="utf-8") as file_txt:
                file_txt.write(str(prod))

        return file_txt_path

    def createJSON(self, mot, entrant, relation):
        """
        Convertit les données TXT en JSON et les stocke.
        """
        file_txt_name = self.createTxt(mot, entrant, relation)
        mot_clean = self.sanitize_filename(mot.replace(" ", "_").replace("'", ""))
        if entrant:
            file_json_name = f"{mot_clean}{relation}_e.json"
        else:
            file_json_name = f"{mot_clean}{relation}_s.json"

        file_json_path = os.path.join(self.cache_dir, file_json_name)

        # Toujours recréer le JSON pour s'assurer qu'il est à jour
        with open(file_txt_name, "r", encoding="utf-8") as file_txt, open(file_json_path, "w",
                                                                          encoding="utf-8") as file_json:
            lines = file_txt.readlines()
            data = {
                "nt": {},
                "e": {},
                "r": {},
                "rt": {}
            }

            fields_nt = ['ntname']
            fields_e = ["name", "type", "w", "formated name"]
            fields_rt = ['trname', 'trgpname', 'rthelp']
            fields_r = ["node1", "node2", "type", "w"]

            for line in lines:
                description = self.convert(line.strip())
                if not description:
                    continue
                if description[0] == "nt":
                    id_nt = description[1]
                    data["nt"][id_nt] = {fields_nt[0]: description[2]}
                elif description[0] == "e":
                    id_e = description[1]
                    data["e"][id_e] = {fields_e[i]: description[i + 2] for i in range(3)}
                    if len(description) > 5:
                        data["e"][id_e][fields_e[3]] = description[5]
                elif description[0] == "rt":
                    id_rt = description[1]
                    data["rt"][id_rt] = {fields_rt[i]: description[i + 2] for i in range(2)}
                    if len(description) > 4:
                        data["rt"][id_rt][fields_rt[2]] = description[4]
                elif description[0] == "r":
                    id_r = description[1]
                    data["r"][id_r] = {fields_r[i]: description[i + 2] for i in range(4)}

            json.dump(data, file_json, indent=4, ensure_ascii=False)

        return file_json_path

    def getData(self, mot, entrant, relation):
        """
        Récupère les données JSON pour un mot donné.
        """
        file_json_name = self.createJSON(mot, entrant, relation)
        with open(file_json_name, "r", encoding="utf-8") as file_json:
            data = json.load(file_json)
        return data

    def idEntite(self, mot, entite, data):
        """
        Récupère les IDs de l'entité et du mot.
        """
        jsonData = data["e"]
        idEntite = -1
        idMot = -1
        for entity_id, entity_info in jsonData.items():
            name = entity_info['name'].replace("'", "")
            if name == entite:
                idEntite = entity_id
            if name == mot:
                idMot = entity_id
        return {"idEntite": idEntite, "idMot": idMot}

    def idRelation(self, relation, data):
        """
        Récupère l'ID de la relation.
        """
        jsonDataRt = data["rt"]
        idRelation = -1
        for entity_id, entity_info in jsonDataRt.items():
            name = entity_info['trname'].replace("'", "")
            if name == relation:
                idRelation = entity_id
                break
        return idRelation

    def isRelationEntrante(self, idEntite, idRelation, data):
        """
        Vérifie si une relation entrante existe.
        """
        jsonDataR = data["r"]
        resultat = False
        w = ""
        for entity_id, entity_info in jsonDataR.items():
            node2 = entity_info['node1'].replace("'", "")
            type_rel = entity_info['type'].replace("'", "")
            w = entity_info["w"]
            if node2 == idEntite and type_rel == idRelation:
                resultat = True
                break
        return [resultat, w]

    def isRelSortantePositive(self, idEntite, idRelation, data):
        """
        Vérifie si une relation sortante positive existe.
        """
        jsonDataR = data["r"]
        for entity_id, entity_info in jsonDataR.items():
            node2 = entity_info['node2'].replace("'", "")
            type_rel = entity_info['type'].replace("'", "")
            if node2 == idEntite and type_rel == idRelation and "-" not in entity_info["w"]:
                return True
        return False

    def isRelSortanteNegative(self, idEntite, idRelation, data):
        """
        Vérifie si une relation sortante négative existe.
        """
        jsonDataR = data["r"]
        for entity_id, entity_info in jsonDataR.items():
            node2 = entity_info['node2'].replace("'", "")
            type_rel = entity_info['type'].replace("'", "")
            if node2 == idEntite and type_rel == idRelation and "-" in entity_info["w"]:
                return True
        return False

    def poids(self, M):
        """
        Retourne le poids d'une relation.
        """
        return int(M[2])

    def getEntiteTransitive(self, data, idRelation, idMot, mot, relation):
        """
        Récupère les entités transitives.
        """
        jsonDataE = data["e"]
        jsonDataR = data["r"]
        resultat = []
        for rel_id, rel_info in jsonDataR.items():
            if rel_info['type'] == idRelation and "-" not in rel_info['w']:
                node2 = rel_info['node2'].replace("'", "")
                if jsonDataE.get(node2, {}).get('type') == '1' and node2 != idMot:
                    resultat.append([node2, jsonDataE[node2]['name'], rel_info['w']])
        resultat = sorted(resultat, key=self.poids, reverse=True)
        if not resultat:
            dataRel = self.getData(mot, True, relation)
            jsonDataE = dataRel["e"]
            jsonDataR = dataRel["r"]
            for rel_id, rel_info in jsonDataR.items():
                if rel_info['type'] == idRelation and "-" not in rel_info['w']:
                    node2 = rel_info['node2'].replace("'", "")
                    if jsonDataE.get(node2, {}).get('type') == '1' and node2 != idMot:
                        resultat.append([node2, jsonDataE[node2]['name'], rel_info['w']])
            resultat = sorted(resultat, key=self.poids, reverse=True)
        return resultat

    def getGenerique(self, data, idMot, mot, relation):
        """
        Récupère les entités génériques.
        """
        dico_generalisation = {"r_isa": "6", "r_holo": "10"}
        if relation in dico_generalisation:
            del dico_generalisation[relation]
        resultat = {}
        for key, id_rel in dico_generalisation.items():
            resultat[key] = self.getEntiteTransitive(data, id_rel, idMot, mot, key)
        return resultat

    def getSpecifique(self, data, idMot, mot, relation):
        """
        Récupère les entités spécifiques.
        """
        dico_specialisation = {"r_hypo": "8", "r_has_part": "9"}
        if relation in dico_specialisation:
            del dico_specialisation[relation]
        resultat = {}
        for key, id_rel in dico_specialisation.items():
            resultat[key] = self.getEntiteTransitive(data, id_rel, idMot, mot, key)
        return resultat

    def check_relation(self, source_word, target_word, relation_code):
        """
        Vérifie si une relation spécifique existe entre deux mots.
        relation_code: Code numérique représentant la relation (ex: 4 pour r_agent, 24 pour r_patient)
        """
        # Récupérer les relations sortantes du source_word pour le type de relation donné
        data = self.fetch_relations(source_word, entrant=False, relation="")
        if not data:
            return False

        # Parcourir les relations pour trouver une correspondance
        for rel_id, rel_info in data.get("r", {}).items():
            if rel_info.get("type") == str(relation_code):
                node2_id = rel_info.get("node2")
                target_info = data.get("e", {}).get(node2_id, {})
                if target_info.get("name", "").lower() == target_word.lower():
                    return True
        return False

# Instance unique de JDMCache (doit être en dehors de la classe)
jdm_cache = JDMCache()


