output "manifest_paths" {
  description = "Paths of the rendered ESO manifests"
  value = [
    local_file.serviceaccount.filename,
    local_file.secretstore.filename,
    local_file.external_secret.filename,
  ]
}
