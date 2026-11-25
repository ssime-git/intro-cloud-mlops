# Étape 1 — Alice arrive

> Avant la démo, slides 13 à 21. Branche : `step-1-identity`.
>
> **▶ Slide 22 · Démo 1 · Alice arrive.**

## À la souris

Console Floci → barre de gauche **Security → Identity** → bouton **Create**.

- Kind : `users`
- Name : `alice`
- **Create**

Alice apparaît dans la liste avec son ARN : `arn:aws:iam::000000000000:user/alice`. On le décode au tableau.

## La même chose en commande

Dans `make shell` :

```bash
# Qui suis-je, moi ? Mon propre ARN.
aws sts get-caller-identity

# Alice, créée à la souris, vue depuis le terminal : même ARN que dans la console
aws iam get-user --user-name alice

# Son badge : AccessKeyId + SecretAccessKey
aws iam create-access-key --user-name alice

# Je mets le badge d'Alice (copier-coller les deux valeurs affichées juste au-dessus)
aws configure set aws_access_key_id     <AccessKeyId>     --profile alice
aws configure set aws_secret_access_key <SecretAccessKey> --profile alice

aws sts get-caller-identity --profile alice     # c'est bien Alice qui parle
aws s3 ls --profile alice
```

Sortie attendue :

```
aws: [ERROR]: An error occurred (AccessDenied) when calling the ListBuckets operation: User is not authorized to perform: s3:ListAllMyBuckets
```

Badge valide, aucune fiche de poste. Et l'erreur nous donne le nom de l'action.

## La fiche de poste d'Alice

> **▶ Slide 23 · Démo 1 · La fiche de poste d'Alice.** On laisse la slide affichée pendant qu'on écrit le JSON.

Méthode en 4 temps :

1. besoin : « Alice doit pouvoir lister les buckets du compte »
2. action : `s3:ListAllMyBuckets` (lue dans l'erreur)
3. ressource : `"*"` (lister les buckets ne vise aucun bucket précis ; la doc le dit)
4. tester : juste après

```bash
mkdir -p policies
cat > policies/list-buckets.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "s3:ListAllMyBuckets",
    "Resource": "*"
  }]
}
JSON

# Je l'accroche à Alice
aws iam put-user-policy --user-name alice --policy-name list-buckets \
  --policy-document file://policies/list-buckets.json

aws s3 ls --profile alice                        # OK : aucune erreur (aucun bucket pour l'instant)
```

Pour comparer, une policy écrite par AWS, beaucoup plus large :

```bash
aws iam get-policy --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
# DefaultVersionId: v3
aws iam get-policy-version --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess --version-id v3
```

```json
"Action": ["s3:Get*", "s3:List*", "s3:Describe*", "s3-object-lambda:Get*", "s3-object-lambda:List*"],
"Effect": "Allow",
"Resource": "*"
```

On la lit ligne par ligne : `Effect`, `Action` (`service:Action`, avec des jokers `*`), `Resource` (`*` = tous les buckets du compte). `Version` est la version du langage des policies, pas une date à mettre à jour.

Puis la capture de l'éditeur visuel du vrai AWS (S3 → List → ListAllMyBuckets) : il produit exactement le JSON écrit plus haut. La console Floci n'a pas cet éditeur.

Console : **Identity** → `alice`. Le détail de l'utilisateur affiche sa policy inline `list-buckets`.

> Le profil `alice` vit dans `~/.aws` du runner. Il disparaît avec le conteneur (`make reset`).
