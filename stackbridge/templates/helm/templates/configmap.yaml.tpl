apiVersion: v1
kind: ConfigMap

metadata:
  name: {{ .Chart.Name }}-config

data:

  ENV: {{ .Values.env | default "development" | quote }}
