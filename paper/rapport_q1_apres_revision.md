# Rapport Q1 après révision majeure de NARCIS

## Verdict

**Soumission défendable comme full research paper, avec recommandation de
minor revision plutôt que major revision.**

La faiblesse la plus bloquante de la version précédente, l'évaluation limitée
à CIFAR-100, est corrigée par une campagne BOSSBase native 512 x 512 sur cinq
partitions. Le manuscrit présente désormais un résultat principal traçable:
1 050 récupérations complètes sur 1 050 essais, sous 21 conditions.

## Contribution et positionnement

La nouveauté ne réside pas dans un nouveau bloc convolutif, AES-GCM ou
Reed-Solomon pris isolément. Elle réside dans la définition et la validation
d'un point de fonctionnement coverless faisable, déterminé conjointement par:

- la stabilité multi-attaque de chaque cover;
- la multiplicité finie de chaque bucket;
- la demande du message protégé;
- la correction d'erreurs;
- la récupération authentifiée du plaintext exact.

Le positionnement exact est donc celui d'un protocole coverless complet et
authentifié. NARCIS ne domine pas les travaux publiés en capacité nominale. Il
apporte en revanche une validation protocolaire plus complète que les
comparaisons Abdulsattar/WYSAWIS examinées dans l'article.

## Évaluation des dimensions

| Dimension | Appréciation |
|---|---|
| Contribution scientifique | Forte et clairement bornée |
| Cohérence scientifique | Forte; claims reliés aux résultats |
| État de l'art | 30 références citées, structuration suffisante |
| Méthode | Architecture et permutation désormais reproductibles |
| Expérimentation | BOSSBase, 5 seeds, 10 messages, 1 050 essais |
| Sécurité | Deux détecteurs; claims correctement limités |
| Présentation | 9 pages double colonne, 5 figures, 3 tableaux |
| Intégrité | Aucun overclaim détecté dans les conclusions |

## Risques résiduels

1. Un reviewer spécialisé peut encore demander SRNet entraîné de bout en bout.
2. BOSSBase reste un corpus unique et grayscale.
3. La comparaison avec les travaux publiés reste méthodologique, faute
   d'implémentations communes évaluées sous le même protocole.
4. Le débit utile des messages courts reste faible en raison des 128 octets de
   parité.

Ces points sont explicitement bornés dans l'article et ne contredisent pas la
contribution revendiquée.

## Recommandation

La cible la plus cohérente reste **Computers & Security** si le papier est
présenté comme protocole sécurisé et validation end-to-end. **Journal of
Information Security and Applications** constitue une cible légèrement moins
risquée. Le manuscrit est publiable; son risque principal n'est plus un manque
de validation élémentaire, mais l'exigence éventuelle d'un benchmark
stéganalytique encore plus spécialisé.
