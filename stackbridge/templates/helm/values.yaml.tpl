replicaCount: 2

image:
  repository: f"docker.io/mykaelhunter/{service_name}"
  tag: latest
  pullPolicy: Always

service:
  port: 80

containerPort: {{PORT}}

env: development
