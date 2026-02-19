# EKS cluster — control plane and managed node groups
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  # Public access allows kubectl from outside the VPC (local machine, CI/CD)
  cluster_endpoint_public_access = true

  # Grants the IAM identity running terraform apply admin access to the cluster
  enable_cluster_creator_admin_permissions = true

  # Disable OIDC provider — using Pod Identity, not IRSA
  enable_irsa = false

  # Tag the node security group so Karpenter can discover it when creating new nodes
  # Karpenter assigns this SG to the EC2 instances it provisions
  node_security_group_tags = {
    "karpenter.sh/discovery" = var.cluster_name
  }

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    # Pod Identity agent — required before any Pod Identity association takes effect
    eks-pod-identity-agent = {
      most_recent = true
    }
    # EBS CSI driver — required to provision EBS volumes for PersistentVolumeClaims
    # Without this, any PVC with storageClassName gp2/gp3 stays in Pending forever
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  eks_managed_node_groups = {
    # System node group — runs Karpenter itself, the LBC, and kube-system pods
    # Karpenter cannot run on nodes it manages, so this group must exist before Karpenter starts
    system = {
      name           = "${var.cluster_name}-system"
      instance_types = [var.instance_type]

      min_size     = var.system_nodes.min
      desired_size = var.system_nodes.desired
      max_size     = var.system_nodes.max

      # Override the auto-generated IAM role name — the default pattern
      # "{cluster}-{group}-eks-node-group-" exceeds the 38-char AWS limit
      iam_role_name            = "${var.cluster_name}-system-ng"
      iam_role_use_name_prefix = false

      # Prevents application pods from landing on system nodes
      taints = {
        CriticalAddonsOnly = {
          key    = "CriticalAddonsOnly"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }

      labels = {
        role = "system"
      }
    }
    # Application nodes are provisioned dynamically by Karpenter — see k8s/karpenter/
  }

  # Allow Karpenter-provisioned nodes to join the cluster
  # EC2_LINUX type automatically grants the standard EKS worker node permissions
  # This replaces the legacy aws-auth ConfigMap approach
  access_entries = {
    karpenter_nodes = {
      principal_arn = aws_iam_role.karpenter_node.arn
      type          = "EC2_LINUX"
    }
  }

  tags = merge(local.tags, {
    # Required by Karpenter to discover the cluster when provisioning nodes
    "karpenter.sh/discovery" = var.cluster_name
  })
}
