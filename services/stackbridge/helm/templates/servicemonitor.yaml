apiVersion: monitoring.coreos.com/v1

kind: ServiceMonitor

metadata:

  name: {{ .Chart.Name }}

  labels:

    # kube-prometheus-stack's Prometheus CR defaults to
    # serviceMonitorSelectorNilUsesHelmValues: true, which restricts
    # discovery to ServiceMonitors carrying this release label — a
    # ServiceMonitor without it is silently never scraped (no error,
    # it just won't show up under Prometheus's Targets page). Must
    # match the release name used in
    # `stackbridge environment bootstrap-monitoring`
    # (core/monitoring.py: MONITORING_RELEASE_NAME). If that install
    # used a different release name, override this label to match, or
    # relax the Prometheus CR's serviceMonitorSelector instead.
    release: kube-prometheus-stack

spec:

  selector:

    matchLabels:

      app: {{ .Chart.Name }}

  endpoints:

  - port: http

    # This assumes the app exposes a Prometheus-format /metrics
    # endpoint on the same port it serves traffic. If it doesn't yet,
    # this ServiceMonitor will just produce scrape errors in
    # Prometheus (visible under Status > Targets) until that's added.
    path: /metrics

    interval: 30s
