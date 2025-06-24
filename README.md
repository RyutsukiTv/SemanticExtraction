# 📚 Analyseur Syntaxique – README

## ⚠️ Problèmes identifiés

### 🧩 1. Fonction de règles (ligne 377)
- **Problème** : Les règles ne tiennent pas compte de l’ordre des types, seulement de leur présence.
- **Conséquence** :  
  - Exemple : `"Le gâteau est posé sur la table"` → erreur `le_est_posé`.
  - Exemple : `"Le gâteau bleu est mangé"` → erreur probable du type `le_bleu_mangé`.

### 🧠 2. Problème lié au dernier GN
- Exemple : `"Le chat mange la souris. Elle est morte"`  
- **Erreur** : Mauvaise gestion des GN (groupes nominaux), le dernier GN n'est pas correctement pris en compte ou mauvaise vérification du node d’origine.

### 🧱 3. Groupe nominal non détecté en entier
- Exemple : `"le petit chat roux"` → [le_petit_chat] + [roux]
- **Cause** : Absence de règle pour traiter ce type de séquence complète.

### 🌐 4. Erreur réseau (rare)
- Exemple : `"ROUGE sa mère c'est écrit"`  
- **Note** : Ce type d’erreur est rare, mais a été observé.

### ❓ 5. Pas de `wordType`
- **Cause** :  
  - Pas de gestion des retours vides.
  - Absence de double vérification dans les réponses de `JDM_api.py`.

---

## ✅ Points positifs

### ♻️ Extensibilité des classes `Node` et `SuperNode`
- Permet l’ajout de nouveaux arguments et paramètres.
- Facilite l’intégration de nouvelles fonctions pour améliorer les traitements syntaxiques et sémantiques.

---

## ❌ Points négatifs

### 🔁 Vérification des règles (ligne 377)
- Les types sont détectés indépendamment de leur ordre.
- **Exemple** : Une règle `Det + Adj` est acceptée même si l’ordre est `Adj + Det`, ce qui est incorrect.

### 🐢 Performance
- Le traitement est **long**, cause non identifiée.

---

## 🛠️ Améliorations proposées

1. Utiliser **pleinement** l’API de **JeuxDeMots (JDM)** – actuellement, le projet repose encore sur la structure de l’année précédente.
2. **Meilleure structuration** du code :
   - Extraire les traitements sous forme de **fonctions claires**.
3. Ajouter les **relations entre le verbe et le node suivant** pour renforcer l’analyse grammaticale.

---

## 🧬 Architecture : Pourquoi `Node` et `SuperNode` ?

- `Node` représente un **mot isolé**.
- `SuperNode` regroupe :
  - les **groupes de mots** (ex. groupes nominaux),
  - ou les **mots seuls** après traitement.

---

## ✅ Exemples qui fonctionnent

- `"Le petit chat boit du lait."`
- `"Le petit chat boit du lait. Il est heureux."`
- `"Le gâteau est délicieux."`
