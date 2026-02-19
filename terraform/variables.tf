variable "region" {
  description = "AWS region where all resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster — also used as a prefix for VPC, IAM, and SQS resources"
  type        = string
  default     = "device-statistics"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.35"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC — subnets are carved out of this range"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type for the system node group — t3.medium is the minimum recommended for EKS"
  type        = string
  default     = "t3.medium"
}

variable "system_nodes" {
  description = "Scaling configuration for the system node group (Karpenter, LBC, and kube-system pods)"
  type = object({
    min     = number
    desired = number
    max     = number
  })
  default = {
    min     = 1
    desired = 2
    max     = 3
  }
}
