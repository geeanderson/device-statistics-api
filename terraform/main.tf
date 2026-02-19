provider "aws" {
  region = var.region
}

# Helm provider — authenticates against EKS using the AWS CLI token
# No static credentials needed; it uses the same credentials as the AWS provider
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.region]
    }
  }
}

# Discover all available AZs in the region — used to spread subnets across zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Common tags applied to every resource — makes filtering by project in the console easier
locals {
  tags = {
    Project     = "device-statistics-api"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
