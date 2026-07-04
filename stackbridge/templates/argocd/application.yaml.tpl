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

    helm:

      parameters:

        - name: env

          value: {{ENVIRONMENT}}

        - name: image.repository

          value: {{IMAGE_REPOSITORY}}

        - name: image.tag

          value: "{{IMAGE_TAG}}"

  destination:

    server: https://kubernetes.default.svc

    namespace: {{NAMESPACE}}

  syncPolicy:

    automated:

      prune: true

      selfHeal: true
