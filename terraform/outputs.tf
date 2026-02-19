output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_version" {
  description = "Kubernetes version running on the cluster"
  value       = module.eks.cluster_version
}

output "cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = module.eks.cluster_endpoint
}

output "vpc_id" {
  description = "VPC ID where the cluster was created"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs — used for node groups and internal services"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs — used for the AWS Load Balancer Controller"
  value       = module.vpc.public_subnets
}

# Run this command after terraform apply to configure kubectl
output "configure_kubectl" {
  description = "Command to configure kubectl access to the cluster"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
