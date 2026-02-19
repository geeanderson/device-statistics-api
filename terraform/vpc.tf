# VPC — all cluster resources live inside this private network
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = var.cluster_name
  cidr = var.vpc_cidr

  # Spread across 3 AZs for high availability
  azs = slice(data.aws_availability_zones.available.names, 0, 3)

  # Private subnets — worker nodes live here, not reachable from the internet
  private_subnets = [for k in range(3) : cidrsubnet(var.vpc_cidr, 4, k)]

  # Public subnets — NAT Gateway and public load balancers live here
  public_subnets = [for k in range(3) : cidrsubnet(var.vpc_cidr, 4, k + 4)]

  # Single NAT Gateway — keeps costs down; fine for this workload
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Tags required by the AWS Load Balancer Controller to discover subnets
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1

    # Karpenter uses this tag to discover which subnets to place new nodes in
    # The value must match the cluster name set in the EC2NodeClass manifest
    "karpenter.sh/discovery" = var.cluster_name
  }

  tags = local.tags
}
