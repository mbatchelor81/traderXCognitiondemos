variable "tenant_id" {
  description = "Tenant identifier injected into every service as the TENANT_ID env var. Must stay underscored."
  type        = string
  default     = "acme_corp"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "demo"
}

variable "region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "cluster_version" {
  description = "Kubernetes control plane version for the EKS cluster."
  type        = string
  default     = "1.34"
}

variable "node_instance_type" {
  description = "EC2 instance type for the managed node group."
  type        = string
  default     = "t3.medium"
}

variable "node_group_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "node_group_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 1
}

variable "node_group_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 4
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

# Port contract — these must agree with each service's Dockerfile EXPOSE, the
# Kubernetes containerPort, and the Service targetPort.
variable "account_service_port" {
  description = "Container port for account-service."
  type        = number
  default     = 8001
}

variable "trading_service_port" {
  description = "Container port for trading-service."
  type        = number
  default     = 8002
}

variable "position_service_port" {
  description = "Container port for position-service."
  type        = number
  default     = 8003
}

variable "reference_data_service_port" {
  description = "Container port for reference-data-service."
  type        = number
  default     = 8004
}

variable "people_service_port" {
  description = "Container port for people-service."
  type        = number
  default     = 8005
}

variable "web_frontend_port" {
  description = "Container port for the nginx-served React frontend."
  type        = number
  default     = 8080
}

locals {
  # TENANT_ID keeps its underscore (acme_corp) because the application expects that
  # exact value, but AWS resource names and DNS-1123 Kubernetes names cannot contain
  # underscores — so every derived name uses the slug form (acme-corp).
  tenant_slug = replace(var.tenant_id, "_", "-")
  name_prefix = "traderx-${local.tenant_slug}"

  # Kubernetes namespace the tenant overlay deploys into (k8s/overlays/acme-corp).
  k8s_namespace = "traderx-${local.tenant_slug}"

  workloads = toset([
    "account-service",
    "trading-service",
    "position-service",
    "reference-data-service",
    "people-service",
    "web-frontend",
  ])

  # ECR repository name per workload: traderx-<workload>-acme-corp
  ecr_repository_names = {
    for w in local.workloads : w => "traderx-${w}-${local.tenant_slug}"
  }

  service_ports = {
    "account-service"        = var.account_service_port
    "trading-service"        = var.trading_service_port
    "position-service"       = var.position_service_port
    "reference-data-service" = var.reference_data_service_port
    "people-service"         = var.people_service_port
    "web-frontend"           = var.web_frontend_port
  }

  common_tags = {
    Application = "traderx"
    Tenant      = var.tenant_id
    Environment = var.environment
  }
}
