# Protocole d'évaluation

Ce fichier fixe les tests avant toute mesure. Le tag Git `prereg-1` date les tests T1 à T4. Aucun d'eux n'a été lancé à cette date, et aucun clip noté n'a été regardé par une méthode.

Tous les seuils de ce fichier sont des choix du projet. Ils ne viennent d'aucune source et ce ne sont pas des résultats. Un seuil franchi est une règle de décision, pas une preuve statistique.

Les tests T5 à T7 seront datés par `prereg-2`, et T8 à T10 par `prereg-3`, avant leur premier lancement.

## Question

Un champ f(x, y, t) ajusté sur une seule vidéo produit-il de vraies images entre deux trames, ou seulement un fondu ? Le champ est comparé à deux références : le cross-fade, qui est le fondu, et RIFE, un interpolateur d'images.

## Données

Une personne, un téléphone, caméra fixe. Chaque clip dure 10 s, à 60 fps, soit 600 trames, avec exposition et mise au point verrouillées.

| Clips | Contenu | Rôle |
|---|---|---|
| C1 | Traversée du cadre | Noté |
| C2 | Geste rapide des bras, hors de la silhouette | Noté |
| C3 | Bras qui passe devant le torse, lentement | Noté |
| C4 | Bras qui passe devant le torse, rapidement | Noté |
| C5 | Cheveux libres, tête qui bouge | Noté |
| C6 | Vêtement proche de la couleur du fond | Noté |
| R1 | Geste moyen, hors de la silhouette | Réglage, jamais noté |
| R2 | Bras devant le torse, vitesse moyenne | Réglage, jamais noté |
| A1 | Ombre portée marquée | Alpha seulement |
| A2 | Personne presque immobile | Alpha seulement |

Le cas du bras devant le torse est attendu comme le plus dur. Il compte parmi les clips notés pour que le verdict ne puisse pas l'éviter.

**Découpage.** Les trames paires, soit 30 fps, servent à l'entraînement. Les trames impaires forment le test : une trame retirée est la vérité au milieu de deux trames gardées. Un second test, sur C2 et C4, ne garde qu'une trame sur quatre.

## Absence de fuite

- L'interpolateur, le flux et l'alpha d'entrée ne reçoivent que les trames d'entraînement.
- L'alpha passe deux fois sur chaque clip noté, car son modèle propage une mémoire entre les trames. La première passe, sur les trames d'entraînement, sert d'entrée. La seconde, sur tout le clip, sert seulement de référence.
- λ, la grille en t et la variante de warping se règlent sur R1 et R2 seulement. L'itération d'arrêt se règle sur un bloc contigu de trames de ces deux clips.
- Aucun réglage n'est fait sur C1 à C6, et aucun clip noté n'est remplacé après la mesure.

## Comparaison à armes égales

- Toutes les méthodes sont notées à une seule résolution, 216×384, après le même recadrage statique.
- Chaque méthode rend une image RGBA, composée sur la même plaque de fond. La référence est la vraie trame, dont le premier plan vient de la passe de référence, composée sur la même plaque.
- Le score sur l'image complète, sans composition, est publié à côté.
- Le fit noté est le fit publié. Le volume du site vient de ce fit, et non d'un fit refait sur toutes les trames.

## Métriques

**Masque de mouvement.** Pixels de la personne dilatée où le flux entre les deux trames d'entraînement voisines dépasse 2,4 px à 384 px de haut, soit 4 px à 640 px. Pour T1, la personne vient de la différence à la plaque. Pour T2 et T3, elle vient de l'alpha de référence.

**PSNR-M.** PSNR dans le masque de mouvement, sur la MSE mise en commun pour tout le clip, en sRGB. Les trames à masque vide sont exclues.

**Plafond de bruit.** PSNR sur le fond entre trames voisines, publié avec chaque tableau. Il donne le niveau au-delà duquel un écart ne veut plus rien dire.

**EPE-M.** Écart moyen, dans le masque de mouvement, entre le flux calculé vers l'image produite et le flux calculé vers la vraie trame. Il est noté avec RAFT de torchvision, qui n'entre dans aucune méthode, car le flux qui entraîne le champ ne peut pas le juger.

**g.** g = (méthode − cross-fade) / (RIFE − cross-fade), en PSNR-M. 0 vaut le cross-fade, 1 vaut RIFE. Il est publié clip par clip, sans seuil, et seulement sur les clips validés par T1.

**β.** β = ⟨G−R, C−R⟩ / ⟨C−R, C−R⟩, avec G l'image produite, R la vraie trame et C le cross-fade, dans le masque de mouvement. β vaut 1 pour le cross-fade et 0 pour une image parfaite. Il mesure le double contour en couleur, car l'alpha vaut 1 sur le bras comme sur le torse et ne voit donc pas un fantôme à l'intérieur de la silhouette.

**Les 10 images de β.** Elles sont choisies par une règle, sans regarder aucune sortie. Pour chaque trame tenue à part de C1 à C6, l'énergie de mouvement est la somme de la norme du flux d'entraînement dans le masque. On prend les 10 trames d'énergie la plus haute, à raison de 3 par clip au plus et avec 20 trames d'écart au moins dans un même clip. La liste est publiée avant le premier fit.

**Appoint.** tOF, LPIPS et FloLPIPS sont publiés sans seuil.

**Lecture.** Les résultats sortent clip par clip, sans moyenne seule, et par bande de déplacement. L'inspection à l'œil des bras, des mains et de l'alpha est obligatoire : le flou de bougé peut pénaliser une sortie plus nette.

## Tests

| Test | Jeu | Mesure | Seuil | Si échec |
|---|---|---|---|---|
| T1 RIFE | C1 à C6 | PSNR-M, EPE-M | Un clip est validé si RIFE gagne au moins 1 dB et si son EPE-M vaut au plus 0,8× celui du cross-fade. T1 réussit si 4 clips sur 6 sont validés | Note contre le seul cross-fade. Le volume reste aux vraies trames |
| T2 Champ, niveau 1 | C1 à C6 | PSNR-M, EPE-M, β | Le critère de T1 tenu sur 4 clips sur 6, β médian ≤ 0,5 sur les 10 images, et gain médian supérieur à l'écart entre deux graines sur C1 | Le champ reste un fondu : le verdict est publié, et les entre-images viennent de RIFE |
| T2 Champ, niveau 2 | C1 à C6 | PSNR-M | Niveau 1 tenu, et moins de 0,5 dB sous RIFE en médiane | Le champ ne porte pas le volume : les entre-images viennent de RIFE |
| T3 Alpha | C1, C5, C6, A1, A2 | Opacité cumulée 1 − Π(1 − α) le long de t hors de la personne dilatée, écart-type temporel sur les zones calmes, vue xt | Sur 4 clips sur 5 : p95 du cumul ≤ 5 % sur 300 tranches, et écart-type ≤ 1/255 | Gating plus strict, fond filmé, autre modèle d'alpha |
| T4 Rendu | Sculpture réelle sur Ryzen 7 5825U, iGPU AMD Barcelo, Chrome en fenêtre réelle | Temps de trame à l'écran, vsync manqués, réglage translucide, sur secteur et sur batterie, avec un cas au zoom ×2 | p95 ≤ 33 ms en 720p interne | Baisser la résolution, puis le nombre de pas, puis la texture |

## Ce que le projet aura le droit d'écrire

- « Sur N clips d'une personne, ce téléphone et ces réglages, le champ se place à g = x de RIFE. »
- « Bat RIFE » ne s'écrit que si g > 1 et si l'EPE-M est sous RIFE sur la majorité des clips validés.
- Le mot « significatif » n'est jamais employé.
- Le test vaut pour 216×384. Il ne dit rien du 720p.

Le verdict est publié dans tous les cas, avec les clips qui échouent.
