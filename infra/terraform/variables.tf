variable "tenant_id" {
  description = "Tenant identifier for single-tenant deployment"
  type        = string
  default     = "acme_corp"
}

variable "environment" {
  description = "Deployment environment (demo, staging, production)"
  type        = string
  default     = "demo"
}

variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "users_service_port" {
  description = "Port for the users service"
  type        = number
  default     = 8001
}

variable "trades_service_port" {
  description = "Port for the trades service"
  type        = number
  default     = 8002
}

variable "frontend_port" {
  description = "Port for the web frontend"
  type        = number
  default     = 8080
}

locals {
  app_name    = "traderx"
  name_prefix = "${local.app_name}-${var.tenant_id}-${var.environment}"
}
