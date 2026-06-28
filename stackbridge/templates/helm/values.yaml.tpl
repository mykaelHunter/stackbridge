replicaCount: 2

image:
  repository: stackbridge/{{SERVICE_NAME}}
  tag: latest
  pullPolicy: Always

service:
  port: 80

containerPort: {{PORT}}
