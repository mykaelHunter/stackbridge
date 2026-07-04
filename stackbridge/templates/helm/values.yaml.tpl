replicaCount: 2

image:
  repository: "{{IMAGE_REPOSITORY}}"
  tag: "{{IMAGE_TAG}}"
  pullPolicy: Always

service:
  port: 80

containerPort: {{PORT}}

# env is intentionally left unset here — it is always supplied at
# deploy time via `helm upgrade --set env=<environment>`
# (see core/helm.py deploy_chart / pipeline/stages/deploy.py), so
# the ConfigMap's ENV always reflects the real target environment
# instead of a value hardcoded once at scaffold time.
