variable "tenant_id" {
  description = "Tenant identifier for resource naming and deployment"
  type        = string
  default     = "test_tenant"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "demo"
}

variable "region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "account_service_port" {
  description = "Port for the Account Service"
  type        = number
  default     = 8001
}

variable "trading_service_port" {
  description = "Port for the Trading Service"
  type        = number
  default     = 8002
}

variable "position_service_port" {
  description = "Port for the Position Service"
  type        = number
  default     = 8003
}

variable "reference_data_service_port" {
  description = "Port for the Reference Data Service"
  type        = number
  default     = 8004
}

variable "people_service_port" {
  description = "Port for the People Service"
  type        = number
  default     = 8005
}
