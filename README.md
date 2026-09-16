# intro-cloud-mlops

Démos pour une masterclass AWS/MLOps utilisant [Floci](https://github.com/floci-io/floci), un émulateur AWS local (alternative open-source à LocalStack), piloté entièrement en conteneurs Docker — rien n'est installé sur la machine hôte.

## Pourquoi Floci ?

Floci tourne en local, gratuitement, et expose une API compatible AWS (S3, Lambda, IAM, DynamoDB, etc.) sur `http://localhost:4566`. Il permet de démontrer des architectures cloud (event-driven, IAM, serverless) sans compte AWS ni coûts.

## Prérequis

- Docker (testé avec [OrbStack](https://orbstack.dev/) sur macOS, mais tout moteur Docker convainc)
- `make`
- [`gh`](https://cli.github.com/) uniquement si vous republiez ce repo

Aucun autre outil n'est requis sur la machine hôte : Python, boto3 et zip tournent dans des conteneurs.

## Démarrage rapide

```bash
make up          # démarre Floci + le conteneur runner Python (boto3)
make demo1        # démo 1 : notification S3 -> Lambda
make demo2        # démo 2 : application des politiques IAM
make down         # arrête et nettoie tout (conteneurs, réseau)
```

## Structure

```
.
├── docker-compose.yml          # Floci + conteneur runner (python:3.12-slim + boto3)
├── Makefile                    # cibles up/down/demo1/demo2/logs/clean
├── demos/
│   ├── 01-s3-lambda-notification/   # dépôt S3 -> déclenchement Lambda automatique
│   └── 02-iam-policy-enforcement/   # refus/autorisation IAM avec policies
└── scripts/                    # utilitaires partagés
```

Chaque démo a son propre `README.md` avec le déroulé pas à pas et le résultat attendu.

## Démo 1 — Notification S3 → Lambda

Une Lambda Python 3.12 (`predict`) est déclenchée automatiquement au dépôt d'un CSV sous `in/` dans le bucket `demo`. Elle ajoute une colonne `prediction` (1 si `score > 0.5`, sinon 0) et écrit le résultat sous `out/`.

Voir [demos/01-s3-lambda-notification/README.md](demos/01-s3-lambda-notification/README.md).

## Démo 2 — Application des politiques IAM

Démontre que Floci applique réellement les policies IAM quand `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true` : un utilisateur `junior` sans permissions se voit refuser `s3:ListAllMyBuckets` (403 `AccessDenied`), puis autorisé après l'attachement d'une policy en ligne.

Voir [demos/02-iam-policy-enforcement/README.md](demos/02-iam-policy-enforcement/README.md).

## Notes / écarts avec AWS réel

- L'application des policies IAM est **désactivée par défaut** dans Floci — sans le flag `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`, tout est autorisé quel que soit l'utilisateur.
- Le premier déclenchement Lambda est plus lent (~30 s) car Floci télécharge l'image runtime `public.ecr.aws/lambda/python:3.12` ; les déclenchements suivants sont rapides.
- La propagation d'une policy IAM est instantanée dans Floci, alors qu'AWS peut introduire un léger délai en conditions réelles.

## Licence

MIT — voir [LICENSE](LICENSE).
