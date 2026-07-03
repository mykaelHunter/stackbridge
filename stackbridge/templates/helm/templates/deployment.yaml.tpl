apiVersion: apps/v1

kind: Deployment

metadata:
  name: {{ .Chart.Name }}

spec:

  replicas: {{ .Values.replicaCount }}

  selector:
    matchLabels:
      app: {{ .Chart.Name }}

  template:

    metadata:

      labels:
        app: {{ .Chart.Name }}

    spec:

      containers:

      - name: {{ .Chart.Name }}

        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"

        ports:

        - containerPort: {{ .Values.containerPort }}

        envFrom:

        - configMapRef:
            name: {{ .Chart.Name }}-config

        # DB_PASS is not templated here (SEC-01: no in-repo default).
        # Sync it from AWS Secrets Manager before deploying, e.g. via
        # External Secrets Operator or the CI/CD pipeline.
        - secretRef:
            name: {{ .Chart.Name }}-db-secret
