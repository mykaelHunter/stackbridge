# Chaos Engineering - StackBridge IDP

## Purpose
Break things on purpose to prove the platform is resilient.

## Experiments

### 1. Pod Kill (Self-Healing)
Tests if rollouts automatically recover from pod failures.

```bash
# Run the experiment
kubectl apply -f chaos/pod-kill-experiment.yaml

# Watch recovery
kubectl get pods -n default -w

Expected Result: New pods created within 30 seconds

2. CPU Stress (Resource Resilience)
Tests if rollouts handle CPU pressure without crashing.

# Run the experiment
kubectl apply -f chaos/cpu-stress-experiment.yaml

# Monitor rollouts
kubectl get rollouts -n default -w

Expected Result: No pod crashes, rollouts remain healthy


3. Freeze Policy Test
Tests if deployment freeze blocks rollouts during incidents.

# Run the test
./chaos/freeze-test.sh

Expected Result: Deployments blocked when frozen=true

