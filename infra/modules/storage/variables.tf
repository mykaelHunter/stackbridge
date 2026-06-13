variable "name" {
  description = "Name prefix"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "purpose" {
  description = "Bucket purpose suffix (e.g. uploads, backups, logs)"
  type        = string
}

variable "noncurrent_version_expiry_days" {
  description = "Days to retain non-current object versions before deletion"
  type        = number
  default     = 90
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
