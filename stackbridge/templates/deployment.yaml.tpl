apiVersion: apps/v1
kind: Deployment

metadata:
  name: {{SERVICE_NAME}}

spec:
  replicas: 1

  selector:
    matchLabels:
      app: {{SERVICE_NAME}}

  template:
    metadata:
      labels:
        app: {{SERVICE_NAME}}

    spec:
      containers:
      - name: {{SERVICE_NAME}}
        image: mykaelhunter/{{SERVICE_NAME}}:latest

        ports:
        - containerPort: {{PORT}}

        envFrom:
        # Non-secret DB_HOST / DB_USER / DB_NAME overrides live here.
        - configMapRef:
            name: {{SERVICE_NAME}}-config
        # DB_PASS (SEC-01: no in-repo default), plus DB_HOST/DB_PORT/
        # DB_USER/DB_NAME sourced from the real RDS instance. This
        # Secret is NOT created directly — it's synced from AWS
        # Secrets Manager by the ExternalSecret in eso/external-secret.yaml.
        # That file (along with eso/serviceaccount.yaml and
        # eso/secretstore.yaml) is rendered by Terraform — see
        # infra/modules/eso-manifests — not by `stackbridge scaffold`.
        # Run `terraform apply` for the target environment, then
        # `kubectl apply -f eso/` before this Deployment. Also
        # requires external-secrets-operator running in the cluster.
        - secretRef:
            name: {{SERVICE_NAME}}-db-secret
