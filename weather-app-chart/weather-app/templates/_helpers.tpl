{{/*
Expand the name to the full name in the format "<release-name>-<chart-name>"
if no full name is provided.
*/}}
{{- define "weather-app.fullname" -}}
  {{- $nameOverride := .Values.nameOverride -}}
  {{- $fullname := default .Chart.Name .Values.fullnameOverride -}}
  {{- if $nameOverride -}}
    {{- $fullname = $nameOverride -}}
  {{- else -}}
    {{- if .Release.Name -}}
      {{- $fullname = printf "%s-%s" .Release.Name $fullname -}}
    {{- end -}}
  {{- end -}}
  {{- $fullname | trunc 63 | trimSuffix "-" -}}
{{- end -}}
