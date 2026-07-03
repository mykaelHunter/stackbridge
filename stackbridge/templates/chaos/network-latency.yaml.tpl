# Chaos Experiment 3: Network Latency Injection via Toxiproxy
# =============================================================
# Hypothesis: Injecting 500ms latency between services produces
# bounded errors in {{SERVICE_NAME}} without cascading failures
# to unrelated services in the namespace.
#
# Configure after pod is Running:
#   kubectl port-forward pod/{{SERVICE_NAME}}-network-chaos 8474:8474
#
#   # Create a proxy pointing at your downstream target
#   curl -X POST http://localhost:8474/proxies \
#     -H "Content-Type: application/json" \
#     -d '{"name":"db","listen":"0.0.0.0:5431","upstream":"postgres:5432","enabled":true}'
#
#   # Inject 500ms latency with 100ms jitter
#   curl -X POST http://localhost:8474/proxies/db/toxics \
#     -H "Content-Type: application/json" \
#     -d '{"name":"latency","type":"latency","attributes":{"latency":500,"jitter":100}}'
#
# Watch: kubectl logs {{SERVICE_NAME}}-network-chaos -c observer
# Measure: p95 latency of {{SERVICE_NAME}}, error rate on endpoints
# Clean: kubectl delete -f chaos/network-latency.yaml
apiVersion: v1
kind: Pod
metadata:
  name: {{SERVICE_NAME}}-network-chaos
  namespace: {{NAMESPACE}}
  labels:
    app: chaos
    experiment: network-latency
    target-service: {{SERVICE_NAME}}
    managed-by: stackbridge-idp
spec:
  restartPolicy: Never
  containers:
    - name: toxiproxy
      image: ghcr.io/shopify/toxiproxy:2.9.0
      ports:
        - containerPort: 8474
          name: toxiproxy-api
        - containerPort: 5431
          name: proxied
      resources:
        requests:
          cpu: "50m"
          memory: "32Mi"
        limits:
          cpu: "100m"
          memory: "64Mi"
    - name: observer
      image: busybox
      command:
        - sh
        - -c
        - |
          echo "Network latency experiment running for {{SERVICE_NAME}}."
          echo "Port-forward to 8474 to configure Toxiproxy."
          sleep 180
          echo "Experiment window closed."
      resources:
        requests:
          cpu: "25m"
          memory: "16Mi"
        limits:
          cpu: "50m"
          memory: "32Mi"
