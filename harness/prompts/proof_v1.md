<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Gabarit d'invite « preuve », version v1 (phase P3, baselines B0–B2). Les lignes de commentaire HTML
     en tête de fichier sont retirées avant l'envoi. Champs remplacés : {{STATEMENT}}, {{HEADER}},
     {{THEOREM}}, {{NAME}}. Toute modification crée une nouvelle version (proof_v2.md…), jamais une
     retouche de celle-ci après le gel. -->
Tu es un expert de Lean 4 et de Mathlib. Prouve le théorème ci-dessous en Lean 4 (Lean v4.35.0, Mathlib et Physlib au tag v4.35.0).

Énoncé informel :
{{STATEMENT}}

Ta solution sera compilée avec exactement l'en-tête suivant. Tes propres lignes `import` seront ignorées, et aucun autre module ne sera disponible :

```lean
{{HEADER}}
```

Énoncé formel à prouver :

```lean
{{THEOREM}}
```

Consignes :
- Réponds par un seul bloc ```lean contenant le théorème complet : la déclaration `theorem {{NAME}}` recopiée à l'identique (même nom, mêmes hypothèses, même conclusion), dont tu remplaces `sorry` par une preuve. Tu peux la faire précéder de lemmes auxiliaires.
- N'utilise ni `sorry`, ni `admit`, ni `native_decide`, ni de déclaration `axiom`, ni `implemented_by`, `extern`, `unsafe` ou `debug.skipKernelTC` : une solution qui en contient est rejetée.
- Seuls les axiomes `propext`, `Quot.sound` et `Classical.choice` sont admis. La solution est vérifiée par le noyau de Lean contre l'énoncé formel ci-dessus.
