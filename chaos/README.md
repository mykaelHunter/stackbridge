# Chaos Engineering - StackBridge IDP

## Purpose
Break things on purpose to prove the platform is resilient.

## Experiments

### 1. Pod Kill (Self-Healing)
kubectl apply -f chaos/pod-kill-experiment.yaml
kubectl get pods -n default -w

### 2. CPU Stress
kubectl apply -f chaos/cpu-stress-experiment.yaml
kubectl get rollouts -n default -w

### 3. Freeze Policy Test
./chaos/freeze-test.sh
