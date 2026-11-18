# Sources tierces d'AMP-Bench-mini

Certains problèmes d'AMP-Bench-mini sont repris de benchmarks publics. Ils restent soumis à la licence de leur source, rappelée dans chaque fichier de problème (champ `[source]`). Les autres sont rédigés par AIM²P et diffusés sous CC BY 4.0.

| Source | Utilisée pour | Licence | Dépôt | Référence |
|---|---|---|---|---|
| miniF2F, version Lean 4 maintenue par Google DeepMind | N3 (olympiades) | Apache-2.0 | https://github.com/google-deepmind/miniF2F | Zheng, Han, Polu, *MiniF2F: a cross-system benchmark for formal Olympiad-level mathematics*, ICLR 2022, [arXiv:2109.00110](https://arxiv.org/abs/2109.00110) |
| ProofNet# (version corrigée de ProofNet) | N4 (premier cycle) | MIT | https://huggingface.co/datasets/PAug/ProofNetSharp | Azerbayev et al., *ProofNet*, [arXiv:2302.12433](https://arxiv.org/abs/2302.12433) ; Poiroux et al., [arXiv:2406.07222](https://arxiv.org/abs/2406.07222) |
| PutnamBench | N4 (Putnam) | Apache-2.0 (énoncés Lean) | https://github.com/trishullab/PutnamBench | Tsoukalas et al., *PutnamBench*, [arXiv:2407.11214](https://arxiv.org/abs/2407.11214) |

**Engagements :**
- Chaque énoncé repris garde l'identifiant de sa source (`source.ref`). Toute modification apportée lors du portage vers Lean v4.35.0 est signalée (`source.modified = true`) et décrite (`audit.notes`).
- Les mainteneurs de PutnamBench demandent de ne pas publier de preuves formelles de ses problèmes. AIM²P ne publiera donc **aucune preuve** des items PutnamBench, seulement les verdicts.
- Les textes des licences Apache-2.0 et MIT sont disponibles dans les dépôts sources ; le texte Apache-2.0 figure aussi dans [LICENSE](LICENSE).
