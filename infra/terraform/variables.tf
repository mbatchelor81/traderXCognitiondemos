variable "tenant_id" {
  description = "Tenant identifier for this deployment"
  type        = string
  default     = "acme_corp"
}

variable "environment" {
  description = "Deployment environment (demo, staging, production)"
  type        = string
  default     = "demo"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "users_service_port" {
  description = "Port for users-service"
  type        = number
  default     = 8001
}

variable "trades_service_port" {
  description = "Port for trades-service"
  type        = number
  default     = 8002
}

variable "frontend_port" {
  description = "Port for frontend (nginx-unprivileged listens on 8080)"
  type        = number
  default     = 8080
}
