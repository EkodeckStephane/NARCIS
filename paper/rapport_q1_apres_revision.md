# Rapport Q1 après traitement des réserves

## Verdict

**Le manuscrit est désormais défendable comme full research paper Q1.**

Les deux réserves expérimentales principales ont été traitées:

- validation sur un second corpus RGB à résolutions variables;
- détecteur CNN appris pour le biais de sélection.

La campagne consolidée couvre 1 575 essais sous 21 conditions, avec
1 575 récupérations authentifiées.

## Positionnement

La contribution n'est pas un record de capacité nominale. Elle établit un
protocole coverless complet dans lequel le point de fonctionnement est choisi
selon la stabilité multi-attaque, la multiplicité finie des buckets, la
demande du message protégé, la correction d'erreurs et la récupération exacte.

| Dimension | État |
|---|---|
| Contribution | Point de fonctionnement protégé et vérifié |
| État de l'art | Taxonomie étendue aux GAN, sémantique et diffusion |
| Généralisation | BOSSBase grayscale et Caltech-101 RGB |
| Robustesse | 1 575 / 1 575 récupérations |
| Détectabilité | Régression, ExtraTrees et CNN sur deux corpus |
| Reproductibilité | Scripts, seeds, tableaux consolidés et figures |

## Risques résiduels

1. Les baselines publiées ne sont pas réimplémentées sous un protocole commun.
2. Caltech-101 est centre-fitté à 256 x 256 pour le batching.
3. Le CNN cible la sélection d'images inchangées et n'est pas une
   réimplémentation de SRNet.
4. Le débit net des messages courts reste réduit par les 128 octets de parité.

Ces limites bornent la portée sans invalider la contribution.

## Recommandation

`Computers & Security` est cohérent si l'accent reste placé sur le protocole,
l'authentification et l'évaluation du biais de sélection. `Journal of
Information Security and Applications` constitue une seconde cible directe.
