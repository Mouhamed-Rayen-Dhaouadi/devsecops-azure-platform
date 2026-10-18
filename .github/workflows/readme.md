# Plateforme DevSecOps sur Azure

![Security checks](https://github.com/Mouhamed-Rayen-Dhaouadi/devsecops-azure-platform/actions/workflows/security.yml/badge.svg)

Ce projet met en place une chaîne d'intégration continue (CI) qui contrôle automatiquement la sécurité du code avant toute fusion dans la branche `main`. Le déploiement automatique sur Azure avec Terraform est la prochaine étape.

L'application contrôlée est une petite API FastAPI. Elle sert de « produit test » : l'objectif du projet est la chaîne de contrôle, pas l'API.

## Architecture de la chaîne CI

```
Développeur → branche → Pull Request → GitHub Actions
                                          ├─ gitleaks  (secrets)
                                          ├─ semgrep   (code et workflow)
                                          ├─ trivy     (image Docker)
                                          └─ tests     (pytest)
                                                │
                              les 4 contrôles sont verts
                                                ▼
                                   fusion autorisée dans main
```

## Les contrôles

| Contrôle | Outil | Ce qu'il détecte | Bloque la fusion si |
|---|---|---|---|
| Secrets | gitleaks | Clés et mots de passe écrits dans le code ou l'historique Git | un secret est trouvé |
| Code et workflow | Semgrep (`p/python`, `p/owasp-top-ten`) | Pratiques dangereuses dans le code et les workflows | un problème est signalé |
| Image Docker | Trivy (`HIGH,CRITICAL`) | Failles connues (CVE) dans l'image | une faille grave corrigeable existe |
| Fonctionnement | pytest | Régressions de l'API | un test échoue |

Chaque action GitHub est **épinglée par son SHA de commit** (et non par un tag) pour éviter qu'une action compromise soit remplacée silencieusement. Le workflow s'exécute avec la permission minimale `contents: read`.

## Protection de la branche `main`

Un ruleset GitHub impose :
- de passer par une **pull request** (aucun push direct) ;
- que les **4 contrôles soient verts** avant la fusion ;
- l'interdiction des **force push**.

![Push direct refusé](docs/push-direct-refuse.png)

## Preuves : les contrôles détectent vraiment

Un contrôle qui reste vert ne prouve pas qu'il fonctionne. J'ai donc vérifié chacun d'eux avec un cas d'échec réel.

### 1. Secrets : deux couches de défense

GitHub Push Protection a bloqué un push contenant de fausses clés AWS, avant même le pipeline.

![Blocage GH013](docs/push-protection-gh013.png)

Un commit contenant une clé est tout de même passé, et gitleaks l'a détecté dans le pipeline.

![gitleaks rouge](docs/gitleaks-rouge.png)

### 2. Semgrep : le workflow lui-même était non conforme

Semgrep a signalé 3 actions GitHub utilisant un tag modifiable (`@v4`, `@v2`), ce qui permet une attaque sur la chaîne d'approvisionnement. Correction : épinglage par SHA.

![Semgrep rouge](docs/semgrep-rouge.png)

### 3. Trivy : image de base vulnérable

Un commit utilisant une image de base ancienne a fait échouer Trivy dans la pull request, et le bouton de fusion est resté bloqué. Retour à `python:3.13-slim`, puis fusion.

![Trivy rouge](docs/trivy-rouge.png)

## Leçons apprises

1. **Supprimer un secret du code ne le retire pas de l'historique Git.** Dans un cas réel, on révoque d'abord la clé, on nettoie ensuite.
2. **Un contrôle vert ne prouve rien tant qu'on ne l'a pas fait échouer.** Mon premier faux secret était une clé d'exemple AWS ignorée par gitleaks.
3. **`.gitleaksignore` réduit une alerte au silence, il ne supprime pas le secret.** Il est réservé aux faux positifs légitimes.
4. **Un contrôle obligatoire doit exister.** Ma règle exigeait un check `tests` qui n'était pas encore défini dans le workflow : les pull requests restaient bloquées en « Expected ».
5. **Les outils de sécurité s'appliquent aussi au pipeline.** Semgrep a trouvé des défauts dans mon propre workflow.

## Lancer le projet en local

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
python -m pytest               # lancer les tests
uvicorn main:app --reload      # lancer l'API
```

Avec Docker :

```bash
docker build -t mon-api .
docker run -p 8000:8000 mon-api
```

L'image s'exécute avec un utilisateur non-root (`appuser`).

## Prochaines étapes

- [ ] Infrastructure Azure décrite avec **Terraform** (réseau, Key Vault, registre d'images)
- [ ] **Checkov** pour contrôler les mauvaises configurations Terraform
- [ ] Déploiement automatique sur Azure avec authentification **OIDC** (aucun secret stocké dans GitHub)
- [ ] Politiques Kubernetes (Kyverno) et supervision (Prometheus, Grafana)