apiVersion: argoproj.io/v1alpha1

kind: Application

metadata:
  name: {{SERVICE_NAME}}

spec:

  project: default

  source:

    repoURL: {{REPO_URL}}

    targetRevision: HEAD

    path: services/{{SERVICE_NAME}}/helm

  destination:

    server: https://kubernetes.default.svc

    namespace: default

  syncPolicy:

    automated:

      prune: true

      selfHeal: true
