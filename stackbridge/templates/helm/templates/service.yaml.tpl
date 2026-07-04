apiVersion: v1

kind: Service

metadata:
  name: {{ .Chart.Name }}

spec:

  selector:
    app: {{ .Chart.Name }}

  ports:

  # Named so ServiceMonitor (helm/templates/servicemonitor.yaml) can
  # target it via spec.endpoints[].port, which selects by port *name*,
  # not number.
  - name: http

    port: {{ .Values.service.port }}

    targetPort: {{ .Values.containerPort }}
