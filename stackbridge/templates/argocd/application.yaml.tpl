apiVersion: argoproj.io/v1alpha1

kind: Application

metadata:
  name: {{SERVICE_NAME}}

spec:

  project: default

  source:

    repoURL: https://github.com/mykaelHunter/stackbridge.git

    targetRevision: HEAD

    path: services/{{SERVICE_NAME}}/helm

  destination:

    server: https://kubernetes.default.svc

    namespace: default

  syncPolicy:

    automated:

      prune: true

      selfHeal: true
