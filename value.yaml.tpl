replicaCount: 2

image:
  repository: ghcr.io/company/{{SERVICE_NAME}}
  tag: latest

service:
  port: {{PORT}}
