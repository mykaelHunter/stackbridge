apiVersion: argoproj.io/v1alpha1
kind: Application

metadata:
  name: {{SERVICE_NAME}}

spec:
  destination:
    namespace: default
    server: https://kubernetes.default.svc

  source:
    repoURL: https://github.com/company/platform-apps
    path: services/{{SERVICE_NAME}}

  project: default

  syncPolicy:
    automated: {}
