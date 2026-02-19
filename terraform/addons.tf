# Karpenter — provisions EC2 nodes dynamically based on pending pod requirements.
# Runs on the system node group; application nodes live in k8s/karpenter/ manifests.
resource "helm_release" "karpenter" {
  name             = "karpenter"
  repository       = "oci://public.ecr.aws/karpenter"
  chart            = "karpenter"
  namespace        = "karpenter"
  version          = "1.9.0"
  create_namespace = true

  # The cluster name Karpenter will manage nodes for
  set {
    name  = "settings.clusterName"
    value = module.eks.cluster_name
  }

  # SQS queue name for interruption handling — must match the queue in sqs.tf
  set {
    name  = "settings.interruptionQueue"
    value = aws_sqs_queue.karpenter.name
  }

  # Service account name — must match the Pod Identity association in iam.tf
  set {
    name  = "serviceAccount.name"
    value = "karpenter"
  }

  # Toleration to run on system nodes (CriticalAddonsOnly:NoSchedule taint)
  set {
    name  = "tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "tolerations[0].operator"
    value = "Exists"
  }

  set {
    name  = "tolerations[0].effect"
    value = "NoSchedule"
  }

  # Pin Karpenter to the system node group
  set {
    name  = "nodeSelector.role"
    value = "system"
  }

  # Must wait for the cluster, Pod Identity association, and SQS queue to exist
  depends_on = [
    module.eks,
    aws_eks_pod_identity_association.karpenter,
    aws_sqs_queue.karpenter,
  ]
}

# AWS Load Balancer Controller — manages ALB/NLB resources from Kubernetes Ingress objects.
resource "helm_release" "lbc" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "3.0.0"

  set {
    name  = "clusterName"
    value = module.eks.cluster_name
  }

  # Service account name — must match the Pod Identity association in iam.tf
  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "region"
    value = var.region
  }

  set {
    name  = "vpcId"
    value = module.vpc.vpc_id
  }

  # Toleration to run on system nodes
  set {
    name  = "tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "tolerations[0].operator"
    value = "Exists"
  }

  set {
    name  = "tolerations[0].effect"
    value = "NoSchedule"
  }

  set {
    name  = "nodeSelector.role"
    value = "system"
  }

  depends_on = [
    module.eks,
    aws_eks_pod_identity_association.lbc,
  ]
}
