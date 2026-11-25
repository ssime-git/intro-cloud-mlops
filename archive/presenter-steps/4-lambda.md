# Étape 4 — Plus de machine : on passe en Python

> Avant la démo, slides 41 à 44. Branche : `step-4-lambda`.
>
> **▶ Slide 45 · Démo 4 · deploy.py, fonction par fonction.**

Fichiers ajoutés : `pipeline/deploy.py`, `pipeline/handler.py` (importe `add_predictions` depuis `scoring/score.py`), et les deux policies de l'étape 3 (`policies/trust-ec2.json`, `policies/scoring-s3.json`).

## Lire deploy.py avant de le lancer

Il fait quatre choses, chacune est un concept déjà vu :

1. `ensure_role()` : une casquette pour Lambda (trust = `lambda.amazonaws.com`).
2. `ensure_function()` : on embauche la fonction, AWS renvoie son ARN.
3. `ensure_permission()` : on autorise S3 à l'appeler (une policy côté fonction).
4. `ensure_notification()` : on donne à S3 l'ARN de la fonction.

Les policies sont là, en dictionnaires Python : c'est le même JSON qu'on écrivait dans le terminal. Celle de la Lambda reprend `scoring-s3.json`, avec en plus le droit d'écrire ses logs.

Aucune adresse de Floci dans le code : boto3 lit `AWS_ENDPOINT_URL`, comme la CLI. Le même fichier tourne tel quel sur le vrai AWS.

## Un fichier tombe, la prédiction sort

> **▶ Slide 46 · Démo 4 · Un fichier tombe, la prédiction sort.** Puis slides 47 (logs) et 48 (le déclencheur décide).

```bash
python pipeline/deploy.py                                  # affiche les ARN créés
```

```
1. role          arn:aws:iam::000000000000:role/scoring-lambda-role
2. function      arn:aws:lambda:us-east-1:000000000000:function:score
3. permission    s3.amazonaws.com may invoke score for arn:aws:s3:::customers-data
4. notification  s3://customers-data/in/* -> score
```

```bash
aws s3 cp data/customers.csv s3://customers-data/in/day2.csv
aws s3 ls s3://customers-data/out/                         # day2.csv apparaît (1 à 3 s ; relancer si vide)
aws s3 cp s3://customers-data/out/day2.csv - | head

aws logs tail /aws/lambda/score                            # ce que la fonction a fait
```

```
... received s3://customers-data/in/day2.csv
... wrote s3://customers-data/out/day2.csv: 8 rows, 4 predicted 1
```

Console :

- **Storage** → clic sur `customers-data` : le panneau **Objects** en bas montre `in/` et `out/` ; clic sur `out` : `customers.csv` (étape 3) et `day2.csv`.
- **Serverless** → clic sur `score` : runtime `python3.12`, handler `handler.handler`, et le badge **Register Trigger (1)** = la notification S3.
- **Identity** → `scoring-lambda-role` à côté de `scoring-ec2-role`.
- **CloudWatch Logs** → clic sur `/aws/lambda/score` → **Run query** : les deux lignes du handler.

> Floci : seules les lignes écrites par le handler (`print`) arrivent dans CloudWatch Logs. Sur AWS, on voit en plus les lignes `START`, `END` et `REPORT` (durée, mémoire, coût facturé).
