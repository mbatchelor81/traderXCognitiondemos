variable "tenant_id" {
  description = "Tenant identifier for resource naming and isolation"
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

variable "account_service_port" {
  description = "Port for account-service"
  type        = number
  default     = 8001
}

variable "trading_service_port" {
  description = "Port for trading-service"
  type        = number
  default     = 8002
}

variable "position_service_port" {
  description = "Port for position-service"
  type        = number
  default     = 8003
}

variable "reference_data_service_port" {
  description = "Port for reference-data-service"
  type        = number
  default     = 8004
}

variable "people_service_port" {
  description = "Port for people-service"
  type        = number
  default     = 8005
}

variable "web_frontend_port" {
  description = "Port for web-frontend"
  type        = number
  default     = 18094
}

locals {
  cluster_name = "traderx-${var.environment}"
  common_tags = {
    Project     = "traderx"
    Environment = var.environment
    TenantID    = var.tenant_id
    ManagedBy   = "terraform"
  }
}
