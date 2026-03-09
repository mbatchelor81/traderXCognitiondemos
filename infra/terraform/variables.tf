variable "tenant_id" {
  description = "Tenant identifier for isolated deployment"
  type        = string
  default     = "acme_corp"
}

variable "environment" {
  description = "Deployment environment"
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
  description = "Port for frontend"
  type        = number
  default     = 80
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "traderx-acme-corp-demo"
}
