#!/bin/bash
# stackbridge-combined.sh - ArgoCD + Rollouts + Chaos Engineering

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "  STACKBRIDGE - ARGOCD + ROLLOUTS + CHAOS ENGINEERING"
echo "═══════════════════════════════════════════════════════════════"
echo ""

NAMESPACE="stackbridge"
ARGOCD_NS="argocd"
ROLLOUT_NAME="stackbridge-flask-freeze"

# ──────────────────────────────────────────────────────────────────
# STEP 1: Fix argocd-app.yaml
# ──────────────────────────────────────────────────────────────────
echo "📁 STEP 1: Updating ArgoCD Application"
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
    repoURL: https://github.com/stackbridge/stackbridge
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
  - name: service-name
  metrics:
  - name: freeze-status
    interval: 30s
    successCondition: result == "false"
    failureCondition: result == "true"
    provider:
      web:
        url: "http://freeze-service/status"
        timeout: 5s
        jsonPath: "{$.isFrozen}"
EOF

kubectl apply -f freeze-analysis-template.yaml -n $NAMESPACE
echo "✅ Analysis Template created"

# ──────────────────────────────────────────────────────────────────
# STEP 3: Fix and Apply Rollout with Freeze
# ──────────────────────────────────────────────────────────────────
echo -e "\n📁 STEP 3: Deploying Rollout with Freeze"
echo "─────────────────────────────────────────────────────────"

cat > fixed-freeze-rollout.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: stackbridge-flask-freeze
  namespace: stackbridge
spec:
  replicas: 5
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
        image: localhost:32000/stackbridge:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_APP
          value: "app.py"
        - name: FLASK_ENV
          value: "production"
  strategy:
    canary:
      steps:
      - setWeight: 25
      - pause: {duration: 30s}
      - setWeight: 50
      - pause: {duration: 30s}
      - setWeight: 75
      - pause: {duration: 30s}
      - setWeight: 100
      analysis:
        templates:
        - templateName: freeze-check
---
apiVersion: v1
kind: Service
metadata:
  name: stackbridge-flask-freeze
  namespace: stackbridge
spec:
  selector:
    app: stackbridge-flask-freeze
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP
EOF

kubectl apply -f fixed-freeze-rollout.yaml
echo "✅ Rollout with freeze deployed"

# ──────────────────────────────────────────────────────────────────
# STEP 4: Deploy Chaos Experiments
# ──────────────────────────────────────────────────────────────────
echo -e "\n🌀 STEP 4: Deploying Chaos Experiments"
echo "─────────────────────────────────────────────────────────"

# Fix AZ Failure Experiment
cat > chaos/az-failure-fixed.yaml << 'EOF'
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: az-failure-chaos
  namespace: stackbridge
spec:
  appinfo:
    appns: stackbridge
    applabel: "app=stackbridge-flask-freeze"
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-delete
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: "30"
        - name: PODS_AFFECTED_PERC
          value: "50"
EOF

# Fix CPU Stress Experiment
cat > chaos/cpu-stress-fixed.yaml << 'EOF'
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: cpu-stress-chaos
  namespace: stackbridge
spec:
  appinfo:
    appns: stackbridge
    applabel: "app=stackbridge-flask-freeze"
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-cpu-hog
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: "60"
        - name: CPU_CORES
          value: "2"
EOF

# Fix Pod Kill Experiment
cat > chaos/pod-kill-fixed.yaml << 'EOF'
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: pod-kill-chaos
  namespace: stackbridge
spec:
  appinfo:
    appns: stackbridge
    applabel: "app=stackbridge-flask-freeze"
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-delete
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: "60"
        - name: PODS_AFFECTED_PERC
          value: "30"
EOF

echo "✅ Chaos experiments deployed"

# ──────────────────────────────────────────────────────────────────
# STEP 5: Run Chaos Tests
# ──────────────────────────────────────────────────────────────────
echo -e "\n🌀 STEP 5: Running Chaos Tests"
echo "─────────────────────────────────────────────────────────"

# Run AZ Failure Test
echo "Test 1: Running AZ Failure Simulation..."
kubectl apply -f chaos/az-failure-fixed.yaml
sleep 10
kubectl get chaosengine az-failure-chaos -n stackbridge

# Run CPU Stress Test
echo -e "\nTest 2: Running CPU Stress Test..."
kubectl apply -f chaos/cpu-stress-fixed.yaml
sleep 10
kubectl get chaosengine cpu-stress-chaos -n stackbridge

# Run Pod Kill Test
echo -e "\nTest 3: Running Pod Kill Test..."
kubectl apply -f chaos/pod-kill-fixed.yaml
sleep 10
kubectl get chaosengine pod-kill-chaos -n stackbridge

# ──────────────────────────────────────────────────────────────────
# STEP 6: Check Status
# ──────────────────────────────────────────────────────────────────
echo -e "\n📊 STEP 6: Deployment Status"
echo "─────────────────────────────────────────────────────────"

echo "ArgoCD Application:"
kubectl get application stackbridge-app -n argocd

echo -e "\nRollout Status:"
kubectl get rollout stackbridge-flask-freeze -n stackbridge

echo -e "\nPods:"
kubectl get pods -n stackbridge | grep flask

echo -e "\nChaos Engines:"
kubectl get chaosengine -n stackbridge

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Useful Commands:"
echo "  Check Rollout:     kubectl get rollout -n stackbridge"
echo "  Check Pods:        kubectl get pods -n stackbridge"
echo "  Check Chaos:       kubectl get chaosengine -n stackbridge"
echo "  Check ArgoCD:      kubectl get application -n argocd"
echo "  Freeze Status:     kubectl get rollout stackbridge-flask-freeze -n stackbridge -o yaml | grep freeze"
echo ""
echo "🔥 Chaos Commands:"
echo "  Run AZ Failure:    kubectl apply -f chaos/az-failure-fixed.yaml"
echo "  Run CPU Stress:    kubectl apply -f chaos/cpu-stress-fixed.yaml"
echo "  Run Pod Kill:      kubectl apply -f chaos/pod-kill-fixed.yaml"
echo "  Check Chaos Logs:  kubectl logs -f -n stackbridge -l chaos"
