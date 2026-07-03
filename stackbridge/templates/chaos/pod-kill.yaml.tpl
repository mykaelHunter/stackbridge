# Chaos Experiment 1: Pod Kill — Self-Healing / AZ Failure
# ==========================================================
# Hypothesis: If pods in {{SERVICE_NAME}} are killed, the rollout
# controller recreates them within 30 seconds and the service
# remains available throughout.
#
# Run:   kubectl apply -f chaos/pod-kill.yaml
# Watch: kubectl get pods -l app={{SERVICE_NAME}} -w
# Clean: kubectl delete -f chaos/pod-kill.yaml
apiVersion: v1
kind: Pod
metadata:
  name: {{SERVICE_NAME}}-pod-kill
  namespace: {{NAMESPACE}}
  labels:
    app: chaos
    experiment: pod-kill
    target-service: {{SERVICE_NAME}}
    managed-by: stackbridge-idp
spec:
  restartPolicy: Never
  serviceAccountName: chaos-sa
  containers:
    - name: chaos
      image: bitnami/kubectl:latest
      command:
        - /bin/sh
        - -c
        - |
          echo "=== Pod Kill Chaos — {{SERVICE_NAME}} ==="
          echo "Deleting pods from {{SERVICE_NAME}}..."
          kubectl get pods -n {{NAMESPACE}} -l app={{SERVICE_NAME}} -o name \
            | head -2 | xargs kubectl delete -n {{NAMESPACE}}
          echo "Pods deleted. Watching recovery..."
          sleep 30
          kubectl get pods -n {{NAMESPACE}} -l app={{SERVICE_NAME}}
          echo "Pod kill experiment complete."
