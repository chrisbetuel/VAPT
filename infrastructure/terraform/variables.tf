variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "vapt-production"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "general_node_group" {
  description = "Configuration for the general workload node group"
  type = object({
    instance_types = list(string)
    desired_size   = number
    min_size       = number
    max_size       = number
  })
  default = {
    instance_types = ["t3.medium", "t3.large"]
    desired_size   = 2
    min_size       = 1
    max_size       = 6
  }
}

variable "scanner_node_group" {
  description = "Configuration for the scanner node group with spot instances"
  type = object({
    instance_types = list(string)
    desired_size   = number
    min_size       = number
    max_size       = number
  })
  default = {
    instance_types = ["c5.2xlarge", "c5d.2xlarge"]
    desired_size   = 2
    min_size       = 1
    max_size       = 10
  }
}

variable "aws_auth_users" {
  description = "List of IAM users to grant cluster access"
  type = list(object({
    userarn  = string
    username = string
    groups   = list(string)
  }))
  default = []
}
