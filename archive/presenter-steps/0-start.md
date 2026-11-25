# Étape 0 — Votre AWS de poche

> Slide 11 · Démo 0. Branche : `step-0-start`.

Sur la machine hôte (Mac, Linux ou WSL), à la racine du repo :

```bash
make up          # Floci 2.5.0 + runner, IAM enforcement activé, images EC2/Lambda/console pré-téléchargées
make console     # ouvre http://localhost:4566/_floci/ui (redirige vers http://localhost:4500)
make shell       # terminal dans le runner : toutes les commandes suivantes se tapent ici
```

Ce qu'on montre :

- La console Floci : `Console Home`, la barre de gauche par famille (Compute, Storage, Security → Identity, Observability → CloudWatch Logs…). En haut à droite : `Connected http://floci:4566`.
- Dans le runner, `aws --version` : c'est la vraie AWS CLI v2. Aucune commande n'a besoin de `--endpoint-url` : la variable `AWS_ENDPOINT_URL=http://floci:4566` envoie tout vers Floci.

Notes :

- Le premier `make up` télécharge environ 1,5 Go (Floci, runner, Amazon Linux 2023, runtime Lambda Python 3.12, console). À faire avant la session.
- La première ouverture de la console démarre un conteneur `floci-aws-ui` : une page « Starting Floci UI… » s'affiche quelques secondes.
- La console et le port 4566 n'écoutent que sur `127.0.0.1` : ils n'ont pas d'authentification.

Changer d'étape (apprenant en retard, ou pour repartir propre) :

```bash
make step S=step-2-ec2     # git checkout -f, après avoir rendu à l'utilisateur les fichiers créés dans le runner
```
