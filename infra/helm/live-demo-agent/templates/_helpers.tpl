{{- define "live-demo-agent.name" -}}
live-demo-agent
{{- end -}}

{{- define "live-demo-agent.labels" -}}
app.kubernetes.io/part-of: live-demo-agent
app.kubernetes.io/managed-by: Helm
{{- end -}}

{{- define "live-demo-agent.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop:
    - ALL
{{- end -}}
