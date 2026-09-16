# Démo 2 — Application des politiques IAM

Démontre que Floci applique réellement les policies IAM quand l'enforcement est activé.

## Prérequis

Floci doit être démarré avec `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`. La cible `make demo2` redémarre le service `floci` avec ce flag automatiquement.

## Déroulé

1. Avec les identifiants admin `test`/`test` (qui contournent l'enforcement), création de l'utilisateur IAM `junior` et de sa clé d'accès.
2. Avec les clés de `junior`, appel de `s3.list_buckets()` → **403 AccessDenied** attendu.
3. Toujours avec `test`/`test`, attachement d'une policy en ligne autorisant `s3:ListAllMyBuckets` sur `*`.
4. Avec les clés de `junior`, nouvel appel `s3.list_buckets()` → succès attendu.

## Lancer la démo

```bash
make up
make demo2
```

## Résultat attendu

```
Step 1: list_buckets() as junior (no policy attached yet) -> expecting AccessDenied
  -> 403 AccessDenied: User is not authorized to perform: s3:ListAllMyBuckets

Attaching inline policy AllowListBuckets (s3:ListAllMyBuckets on *)...

Step 2: list_buckets() as junior again -> expecting success
  -> SUCCESS after 0.01s, buckets: []
```

## Point pédagogique

- Sans `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`, **toutes** les actions sont autorisées quels que soient les identifiants — l'enforcement IAM est désactivé par défaut.
- La propagation d'une policy est instantanée dans Floci, contrairement à AWS réel où un léger délai de propagation peut être observé.
