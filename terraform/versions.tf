terraform {
  required_version = ">= 1.9.0"

  required_providers {
    # AWS provider — manages all AWS resources (VPC, EKS, IAM, etc.)
    # Constrained to 5.x: terraform-aws-modules/eks ~> 20.0 requires < 6.0.0
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    # Helm provider — deploys Kubernetes applications (Karpenter, LBC)
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }

    # Local provider — generates k8s manifests from templates with Terraform values
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
