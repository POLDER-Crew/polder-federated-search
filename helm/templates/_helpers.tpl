{{/*
Expand the name of the chart.
*/}}
{{- define "polder-federated-search.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "polder-federated-search.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "gleaner.fullname" -}}
{{- if contains "gleaner" .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name "gleaner" | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}


{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "polder-federated-search.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "polder-federated-search.labels" -}}
helm.sh/chart: {{ include "polder-federated-search.chart" . }}
{{ include "polder-federated-search.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "gleaner.labels" -}}
helm.sh/chart: {{ include "polder-federated-search.chart" . }}
{{ include "gleaner.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "polder-federated-search.selectorLabels" -}}
app.kubernetes.io/name: {{ include "polder-federated-search.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "gleaner.selectorLabels" -}}
app.kubernetes.io/name: gleaner
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "polder-federated-search.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "polder-federated-search.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Complicated service URLS
*/}}
{{- define "gleaner.triplestore.endpoint" -}}
http://triplestore-svc.{{ .Release.Namespace }}.svc.cluster.local:{{ .Values.triplestore_service.port }}/bigdata/
{{- end }}
{{- define "gleaner.s3system.endpoint" -}}
s3system-svc.{{ .Release.Namespace }}.svc.cluster.local
{{- end }}

{{/* Volume claim locations
*/}}
{{- define "gleaner.persistentStorage.triplestore" -}}
{{- if .Values.persistence.existing }}
polder-pvc-01
{{- else }}
local-volume-triplestore
{{- end }}
{{- end }}

{{- define "gleaner.persistentStorage.s3system" -}}
{{- if .Values.persistence.existing }}
polder-pvc-02
{{- else }}
local-volume-s3system
{{- end }}
{{- end }}
