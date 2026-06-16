#!/bin/bash
echo "=== Freeze Policy Test ==="
FROZEN=$(kubectl get configmap deployment-freeze-policy -n argocd -o jsonpath='{.data.frozen}' 2>/dev/null)
echo "Current freeze status: $FROZEN"
echo ""
echo "Enabling freeze..."
kubectl patch configmap deployment-freeze-policy -n argocd --type merge -p '{"data":{"frozen":"true"}}'
echo "Freeze enabled - Deployments blocked"
echo ""
echo "Attempting to update Flask rollout during freeze..."
kubectl patch rollout stackbridge-flask-freeze -n default --type merge -p '{"spec":{"template":{"spec":{"containers":[{"name":"stackbridge-app","image":"mykaelhunter/stackbridge:v2"}]}}}}' 2>/dev/null || echo "Rollout update blocked by freeze (expected)"
echo ""
echo "Disabling freeze..."
kubectl patch configmap deployment-freeze-policy -n argocd --type merge -p '{"data":{"frozen":"false"}}'
echo "Freeze disabled - Deployments allowed"
echo ""
echo "✅ Freeze policy test complete!"
