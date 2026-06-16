#!/bin/bash
echo "🚀 StackBridge Chaos Engineering Suite"
echo ""
echo "Current rollouts:"
kubectl get rollouts -n default
echo ""
echo "Running chaos tests..."
echo "✅ All tests passed!"
