# Étape 5 — L'architecture finale, et la quatrième façon

> Avant, slides 49 à 54 : les autres maisons (pas de démo). Branche : `step-5-final`.
>
> Slides 56 à 58 : les 5 questions, rejouées, puis l'architecture finale. Sur la 58, on bascule dans la console.

## L'architecture finale dans la console

On rejoue les 5 questions sur ce qui est affiché :

| Question | Où on le voit |
|---|---|
| Qu'est-ce qui déclenche le travail ? | **Storage** → `customers-data` : un fichier dans `in/` |
| Où vivent les données ? | **Storage** → `customers-data` : `in/` et `out/` |
| Qui a le droit de faire quoi ? | **Identity** → `scoring-lambda-role`, `scoring-ec2-role`, `alice` |
| Qu'est-ce que je paie quand rien ne se passe ? | **Compute** : aucune instance `running`. **Serverless** → `score` : rien ne tourne entre deux fichiers |
| Comment je sais que ça marche ? | **CloudWatch Logs** → `/aws/lambda/score` |

## La quatrième façon : décrire l'état voulu

> **▶ Slide 59 · La quatrième façon.** Puis 60 à 63 sans démo.

On affiche `infra/main.tf` sans le lancer : le bucket et le rôle de l'étape 3 en Terraform. Les JSON écrits à la main pendant la session sont réutilisés tels quels (`file(".../policies/trust-ec2.json")`).

Avec le clic, la commande et le code, on décrit des **étapes** (« crée ceci, puis attache cela »). Avec Terraform, on décrit **l'état voulu**, et l'outil calcule les étapes.

## Fin

```bash
exit
make down       # supprime Floci, le runner, les instances EC2, les conteneurs Lambda et la console
```
