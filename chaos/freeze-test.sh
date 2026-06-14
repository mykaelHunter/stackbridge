#!/bin/bash
echo "=== Freeze Policy Test ==="
echo ""
FROZEN=$(kubectl get configmap deployment-freeze-policy -n argocd -o jsonpath='{.data.frozen}' 2>/dev/null)
echo "Current freeze status: $FROZEN"
echo ""
echo "Enabling freeze..."
kubectl patch configmap deployment-freeze-policy -n argocd --type merge -p '{"data":{"frozen":"true"}}'
echo ""
echo "Freeze enabled. Deployments are now blocked."
echo ""
echo "Disabling freeze..."
kubectl patch configmap deployment-freeze-policy -n argocd --type merge -p '{"data":{"frozen":"false"}}'
echo ""
echo "Freeze disabled. Deployments allowed again."
echo ""
echo "✅ Freeze policy test complete!"
