# Étape 3 — Les données sortent de la machine

> Avant la démo, slides 33 à 35. Branche : `step-3-s3-role`.
>
> **▶ Slide 36 · Démo 3 · Un bucket, une machine sans badge.**

Fichier ajouté : `scoring/install.sh` (installe la CLI AWS sur la machine au démarrage). Les deux policies de l'étape s'écrivent en direct.

## Un bucket, une machine sans badge

```bash
# Les données sortent de la machine
aws s3 mb s3://customers-data
aws s3 cp data/customers.csv s3://customers-data/in/customers.csv
aws s3 ls s3://customers-data --recursive

# Une nouvelle machine, avec la CLI AWS installée au démarrage (user data)
ID=$(aws ec2 run-instances --image-id ami-amazonlinux2023 --instance-type t3.micro \
      --key-name ml-key --user-data file://scoring/install.sh \
      --query 'Instances[0].InstanceId' --output text)
IP=$(aws ec2 describe-instances --instance-ids $ID \
      --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
echo $ID $IP
```

Compter **environ 40 s** : SSH, puis l'installation de la CLI par `install.sh`. On commente la slide pendant ce temps.

```bash
scp -i ml-key.pem scoring/score.py root@$IP:
ssh -i ml-key.pem root@$IP
```

Sur la machine :

```bash
aws --version          # si "command not found" : install.sh tourne encore, attendre 10 s
aws s3 cp s3://customers-data/in/customers.csv .
# fatal error: Unable to locate credentials
exit
```

La machine n'a pas de badge.

## Écrire la casquette

> **▶ Slide 37 · Démo 3 · Écrire la casquette.** Le tableau de traduction est à l'écran pendant qu'on tape.

Retour dans le runner. Une casquette, c'est deux policies : **qui** a le droit de l'enfiler, et **ce qu'elle permet**.

Première policy, la trust policy. Besoin : « le service EC2 a le droit d'enfiler cette casquette ».

```bash
cat > policies/trust-ec2.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
JSON
```

Deuxième policy, ce que la casquette permet :

| Dans la phrase | Devient |
|---|---|
| lire | `s3:GetObject` |
| les fichiers de `in/` du bucket `customers-data` | `arn:aws:s3:::customers-data/in/*` |
| écrire | `s3:PutObject` |
| dans `out/` | `arn:aws:s3:::customers-data/out/*` |

```bash
cat > policies/scoring-s3.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::customers-data/in/*" },
    { "Effect": "Allow", "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::customers-data/out/*" }
  ]
}
JSON

aws iam create-role --role-name scoring-ec2-role \
  --assume-role-policy-document file://policies/trust-ec2.json
aws iam put-role-policy --role-name scoring-ec2-role --policy-name scoring-s3 \
  --policy-document file://policies/scoring-s3.json

# Le porte-casquette (instance profile) qu'on accroche à la machine
aws iam create-instance-profile --instance-profile-name scoring-ec2
aws iam add-role-to-instance-profile --instance-profile-name scoring-ec2 --role-name scoring-ec2-role
aws ec2 associate-iam-instance-profile --instance-id $ID --iam-instance-profile Name=scoring-ec2
```

## Les clés temporaires, un refus voulu

> **▶ Slide 38 · Démo 3 · Les clés temporaires, un refus voulu.**

```bash
ssh -i ml-key.pem root@$IP
```

Sur la machine :

```bash
# Les clés temporaires sont là, avec une date d'expiration. Personne ne les a copiées.
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/scoring-ec2-role

aws sts get-caller-identity          # assumed-role/scoring-ec2-role/<ID>
aws s3 cp s3://customers-data/in/customers.csv .
python3 score.py customers.csv out.csv
aws s3 cp out.csv s3://customers-data/out/customers.csv

# Le 4e temps de la méthode, en vrai : on essaie une action non prévue
aws s3 ls s3://customers-data/in/
# AccessDenied ... User is not authorized to perform: s3:ListBucket
# On ne l'a pas demandé, et le scoring n'en a pas besoin. On ne l'ajoute pas.
exit
```

```bash
aws ec2 terminate-instances --instance-ids $ID
aws s3 ls s3://customers-data/out/      # le résultat a survécu à la machine
```

> **▶ Slide 39 · Une machine payée pour 2 secondes.**

Il reste un problème : on paie une machine pour 2 secondes de calcul, et c'est moi qui la lance.

> Floci : `install.sh` écrit aussi `endpoint_url = http://floci:4566` dans `/root/.aws/config` de l'instance, pour que sa CLI parle à Floci et pas au vrai AWS. Sur une vraie instance EC2, on retire ces lignes.
