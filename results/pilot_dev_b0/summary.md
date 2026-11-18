# Résumé de la campagne `pilot_dev_b0`

Taux de réussite vérifiée (moyenne des proportions par problème), IC de Wilson à 95 % sur n problèmes.

| Niveau | B0 | B1 (pass@5, indicatif) | B2 |
|---|---|---|---|
| N1 | 100 % [21 ; 100] (n = 1) | n/d | n/d |
| N2 | 100 % [21 ; 100] (n = 1) | n/d | n/d |
| N3 | 100 % [34 ; 100] (n = 2) | n/d | n/d |
| N5 | 100 % [21 ; 100] (n = 1) | n/d | n/d |
| Tous | 100 % [57 ; 100] (n = 5) | n/d | n/d |

## Générations

| Génération | Niveau | Type | Verdict | Classe d'erreur | Latence API (s) | Comparateur (s) | De bout en bout (s) | Tokens | Fin | Modèle renvoyé | Fournisseur |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEV-01|r1|s1 | N3 | proof | accepted | — | 19.952 | 10.13 | 30.19 | 408+1478 (raisonnement 1134) | stop | nvidia/nemotron-3-ultra-550b-a55b:free | Nvidia |
| DEV-02|r1|s1 | N3 | proof | accepted | — | 52.814 | 9.95 | 62.87 | 408+5751 (raisonnement 5059) | stop | nvidia/nemotron-3-ultra-550b-a55b:free | Nvidia |
| DEV-03|r1|s1 | N1 | answer | correct | — | 5.827 | — | 5.9 | 215+479 (raisonnement 366) | stop | nvidia/nemotron-3-ultra-550b-a55b:free | Nvidia |
| DEV-04|r1|s1 | N2 | answer | correct | — | 8.191 | — | 8.23 | 219+894 (raisonnement 648) | stop | nvidia/nemotron-3-ultra-550b-a55b:free | Nvidia |
| DEV-05|r1|s1 | N5 | answer | correct | — | 117.205 | — | 117.27 | 463+11806 (raisonnement 11506) | stop | nvidia/nemotron-3-ultra-550b-a55b:free | Nvidia |

## Exploitation

- générations notées : 5
- verdicts : {'accepted': 2, 'correct': 3}
- classes d'erreur : {}
- taxonomie (document 04, §5.4) : {}
- modèles renvoyés : {'nvidia/nemotron-3-ultra-550b-a55b:free': 5}
- fournisseurs : {'Nvidia': 5}
- tokens : 1713 en entrée, 20408 en sortie
- à auditer à la main (needs_audit) : aucune
