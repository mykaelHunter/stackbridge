apiVersion: v1
kind: ConfigMap

metadata:
  name: {{SERVICE_NAME}}-config

data:

  # ENV is deliberately left unrendered here, same convention as
  # {{NAMESPACE}} in the chaos manifests — this k8s/ manifest is a
  # plain reference/manual-apply copy (the real deploy path is the
  # Helm chart, see helm/templates/configmap.yaml.tpl), so ENV is
  # substituted at apply time for whichever environment you're
  # targeting rather than being baked in once at scaffold time.
  ENV: {{ENV}}
