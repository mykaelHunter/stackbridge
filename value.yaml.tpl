replicaCount: 2

image:
  repository:  {{IMAGE_REPOSITORY}}
  tag: {{IMAGE_TAG}}
  pullPolicy: IfNotPresent

service:
  port: {{PORT}}
