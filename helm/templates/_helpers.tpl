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
http://triplestore-svc.{{ .Release.Namespace }}.svc.cluster.local:{{ .Values.triplestore_service.port }}
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

{{/*
Partials for commonly used containers
*/}}
{{- define "get-contextfiles" -}}
- name: get-contextfiles
  image: curlimages/curl:7.88.1
  command:
  - curl
  - -O
  - https://schema.org/version/latest/schemaorg-current-https.jsonld
  volumeMounts:
  - name: gleaner-context
    mountPath: /context
  workingDir: /context
{{- end }}

{{- define "gleaner-index" }}
- name: gleaner-index
  image: nsfearthcube/gleaner:v3.0.8
  imagePullPolicy: {{ .Values.image.pullPolicy }}
  args:
  - -cfg
  - gleaner
  env:
  - name: MINIO_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        key:  minioAccessKey
        name: {{ .Release.Name }}-secrets
  - name: MINIO_SECRET_KEY
    valueFrom:
      secretKeyRef:
        key:  minioSecretKey
        name: {{ .Release.Name }}-secrets
  - name: MINIO_ROOT_USER
    valueFrom:
      secretKeyRef:
        key:  minioAccessKey
        name: {{ .Release.Name }}-secrets
  - name: MINIO_ROOT_PASSWORD
    valueFrom:
      secretKeyRef:
        key:  minioSecretKey
        name: {{ .Release.Name }}-secrets
  volumeMounts:
  - name: gleaner-config
    mountPath: /config/gleaner.yaml
    subPath: gleaner.yaml
  - name: gleaner-context
    mountPath: /config
  workingDir: /config
{{- end }}

{{- define "write-to-triplestore" }}
- name: write-to-triplestore
  image: minio/mc:RELEASE.2022-11-17T21-20-39Z
  imagePullPolicy: {{ .Values.image.pullPolicy }}
  workingDir: /config
  volumeMounts:
  - name: polder-repo-config
    mountPath: /config
  command:
  - sh
  - -c
  - ./write-to-triplestore.sh
  env:
  - name: GLEANER_ENDPOINT_URL
    value: {{ include "gleaner.triplestore.endpoint" . }}/repositories/{{ .Values.storageNamespace }}
  - name: GRAPHDB_REST_URL
    value: {{ include "gleaner.triplestore.endpoint" . }}/rest
  - name: GRAPHDB_INDEXER_USER
    value: indexer-user
  - name: GRAPHDB_INDEXER_PASSWORD
    valueFrom:
      secretKeyRef:
        key:  graphdbIndexerPassword
        name: {{ .Release.Name }}-secrets
  - name: MINIO_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        key:  minioAccessKey
        name: {{ .Release.Name }}-secrets
  - name: MINIO_SECRET_KEY
    valueFrom:
      secretKeyRef:
        key:  minioSecretKey
        name: {{ .Release.Name }}-secrets
  - name: MINIO_SERVER_HOST
    value: http://{{ include "gleaner.s3system.endpoint" . }}
  - name: MINIO_SERVER_PORT
    value: "{{ .Values.s3system_service.api_port }}"
  - name: STORAGE_BUCKET
    value: "{{ .Values.storageNamespace }}"
{{- end }}

{{- define "polder-repo-config-volume" }}
- name: polder-repo-config
  configMap:
    name: polder-repo-config
    defaultMode: 0777
{{- end }}
