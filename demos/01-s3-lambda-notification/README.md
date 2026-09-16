# Démo 1 — Notification S3 → Lambda

Une Lambda Python 3.12 (`predict`) est déclenchée automatiquement par une notification S3 quand un objet est créé sous le préfixe `in/` du bucket `demo`. Elle lit le CSV, ajoute une colonne `prediction` (`1` si `score > 0.5`, sinon `0`), et écrit le résultat sous `out/` avec le même nom de fichier.

## Ressources créées

- Rôle IAM `lambda-exec-role` (trust policy `lambda.amazonaws.com`)
- Fonction Lambda `predict` (runtime `python3.12`, zip, timeout 60s)
- Bucket S3 `demo`
- Permission Lambda `lambda:InvokeFunction` pour le principal `s3.amazonaws.com`
- Notification S3 `s3:ObjectCreated:*` filtrée sur le préfixe `in/`

## Lancer la démo

```bash
make up
make demo1
```

Équivalent manuel :

```bash
docker compose exec -T runner python demos/01-s3-lambda-notification/deploy.py
docker compose exec -T runner python demos/01-s3-lambda-notification/trigger_and_wait.py
```

## Résultat attendu

```
score,prediction
0.9,1
0.2,0
0.7,1
```

Délai typique observé : ~30 s au premier déclenchement (téléchargement de l'image runtime Lambda `public.ecr.aws/lambda/python:3.12`), nettement plus rapide ensuite.
