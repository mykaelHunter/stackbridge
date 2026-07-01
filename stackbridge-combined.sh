#!/bin/bash
# stackbridge-combined.sh - ArgoCD + Rollouts + Chaos Engineering

set -e

echo " "
echo "    STACKBRIDGE - ARGOCD + ROLLOUTS + CHAOS ENGINEERING"
echo " "
echo " "
echo ""

NAMESPACE="stackbridge"
ARGOCD_NS="argocd"
ROLLOUT_NAME="stackbridge-flask-freeze"

# ──────────────────────────────────────────────────────────────────
# STEP 1: Apply ArgoCD Application
# ──────────────────────────────────────────────────────────────────
echo -e "\n📁 STEP 1: Applying ArgoCD Application"
echo "─────────────────────────────────────────────────────────"

cat > argocd-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: stackbridge-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/mykaelHunter/stackbridge.git
    targetRevision: HEAD
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: stackbridge
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
EOF

kubectl apply -f argocd-app.yaml
echo "✅ ArgoCD Application applied"

# ──────────────────────────────────────────────────────────────────
# STEP 2: Create Freeze Analysis Template
# ──────────────────────────────────────────────────────────────────
echo -e "\n📁 STEP 2: Creating Freeze Analysis Template"
echo "─────────────────────────────────────────────────────────"

cat > freeze-analysis-template.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: freeze-check
  namespace: stackbridge
spec:
  args:
  - name: freeze-configmap
    value: deployment-freeze-policy
  - name: freeze-namespace
    value: argocd
  metrics:
  - name: check-freeze
    interval: 30s
    successCondition: result == "false"
    failureLimit: 1
    provider:
      job:
        spec:
          backoffLimit: 0
          template:
            spec:
              serviceAccountName: argo-rollouts
              restartPolicy: Never
              containers:
              - name: checker
                image: bitnami/kubectl:latest
                command:
                - /bin/sh
                - -c
                - |
                  FROZEN=$(kubectl get configmap ${ARGS_freeze-configmap} -n ${ARGS_freeze-namespace} -o jsonpath='{.data.frozen}')
                  if [ "$FROZEN" = "true" ]; then
                    echo "Deployment freeze is ACTIVE - blocking rollout"
                    exit 1
                  else
                    echo "false"
                    exit 0
                  fi
                env:
                - name: ARGS_freeze-configmap
                  value: "{{args.freeze-configmap}}"
                - name: ARGS_freeze-namespace
                  value: "{{args.freeze-namespace}}"
EOF

kubectl apply -f freeze-analysis-template.yaml
echo "✅ Freeze Analysis Template applied"

# ──────────────────────────────────────────────────────────────────
# STEP 3: Create Freeze Policy ConfigMap
# ──────────────────────────────────────────────────────────────────
echo -e "\n📁 STEP 3: Creating Freeze Policy ConfigMap"
echo "─────────────────────────────────────────────────────────"

cat > freeze-configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: deployment-freeze-policy
  namespace: argocd
data:
  frozen: "false"
EOF

kubectl apply -f freeze-configmap.yaml
echo "✅ Freeze Policy ConfigMap applied"

# ──────────────────────────────────────────────────────────────────
# STEP 4: Apply Nginx Rollout (Stable)
# ──────────────────────────────────────────────────────────────────
echo -e "\n📁 STEP 4: Applying Nginx Rollout"
echo "─────────────────────────────────────────────────────────"

cat > stackbridge-nginx-fixed.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: stackbridge-flask
  namespace: default
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 10s}
      - setWeight: 50
      - pause: {duration: 10s}
      - setWeight: 100
  selector:
    matchLabels:
      app: stackbridge-flask
  template:
    metadata:
      labels:
        app: stackbridge-flask
    spec:
      containers:
      - name: stackbridge-app
        image: nginx:alpine
        ports:
        - containerPort: 80
EOF

kubectl apply -f stackbridge-nginx-fixed.yaml
echo "✅ Nginx Rollout applied"

# ──────────────────────────────────────────────────────────────────
# STEP 5: Apply Freeze Rollout
# ──────────────────────────────────────────────────────────────────
echo -e "\n📁 STEP 5: Applying Freeze Rollout"
echo "─────────────────────────────────────────────────────────"

cat > fixed-freeze-rollout.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: stackbridge-flask-freeze
  namespace: default
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 10s}
      - setWeight: 50
      - pause: {duration: 10s}
      - setWeight: 100
      analysis:
        templates:
        - templateName: freeze-check
  selector:
    matchLabels:
      app: stackbridge-flask-freeze
  template:
    metadata:
      labels:
        app: stackbridge-flask-freeze
    spec:
      containers:
      - name: stackbridge-app
        image: nginx:alpine
        ports:
        - containerPort: 80
EOF

kubectl apply -f fixed-freeze-rollout.yaml
echo "✅ Freeze Rollout applied"

# ──────────────────────────────────────────────────────────────────
# STEP 6: Summary
# ──────────────────────────────────────────────────────────────────
echo -e "\n=========================================="
echo "   ✅ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "📊 Rollouts:"
kubectl get rollouts -n default
echo ""
echo "📊 Pods:"
kubectl get pods -n default | grep flask
echo ""
echo "🔗 ArgoCD: https://localhost:30352"
echo "👤 Username: admin"
echo "🔑 Password: LIznzN2f1IvcO7FE"
echo ""
