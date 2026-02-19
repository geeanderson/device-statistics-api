# Generates the EC2NodeClass manifest with the correct cluster name and node role.
#
# The file is written to k8s/karpenter/ec2nodeclass.yaml after every terraform apply.
# This eliminates any hardcoded placeholder values in the Kubernetes manifests.
resource "local_file" "ec2nodeclass" {
  filename = "${path.root}/../k8s/karpenter/ec2nodeclass.yaml"

  content = templatefile("${path.module}/templates/ec2nodeclass.yaml.tpl", {
    cluster_name = var.cluster_name
    node_role    = aws_iam_role.karpenter_node.name
  })
}
