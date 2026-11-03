# Continuum

Continuum transforme une courte vidéo de téléphone en objet qu'on regarde dans le navigateur, avec le temps comme troisième dimension.

> **En cours. Rien n'est mesuré pour l'instant.** Aucun chiffre de performance n'existe encore, et ce dépôt n'en affichera aucun qui ne vienne d'une mesure publiée ici.

## Ce que le projet vise

Une vidéo de 10 s, caméra fixe, une personne. Un réseau de neurones apprend cette vidéo comme une fonction f(x, y, t) vers une couleur et une opacité, puis le résultat est précalculé et affiché en WebGL, sans serveur.

Cinq fonctions sont prévues :

1. **Sculpture du temps :** la personne en volume translucide.
2. **Plan de coupe :** droit, oblique ou le long du temps.
3. **Questions en français :** une question allume le passage correspondant dans le volume.
4. **Comparaison de deux gestes :** pose, alignement temporel, différences colorées.
5. **Relief :** une profondeur estimée donne du relief à un instant choisi.

## La question de départ

Un réseau qui apprend une vidéo produit-il de vraies images entre deux trames, ou seulement un fondu ? Le projet mesure ce champ contre le cross-fade et RIFE, sur des trames tenues à part, et publie le verdict même s'il est négatif.

Le protocole et ses seuils sont fixés avant toute mesure, dans [docs/EVALUATION.md](docs/EVALUATION.md). Ce qui n'est pas mesuré est listé dans [docs/LIMITS.md](docs/LIMITS.md).

## Résultats

Ce bloc est produit par `python -m continuum.registry` à partir de `results/`. Un test bloque toute mesure écrite ailleurs.

<!-- résultats : début -->
Aucun résultat publié pour l'instant.
<!-- résultats : fin -->

## Lancer les tests

```bash
make setup
make check
```

## Voir la page de démonstration

```bash
make planes-demo
make bake-demo
make web
```

Elle montre un clip de synthèse en 64 plans ou en volume continu. Aucun chiffre n'en sort.

## Licence

Le code est sous licence MIT. Les modèles tiers gardent leur propre licence, voir [NOTICES](NOTICES). Le projet est non commercial.
