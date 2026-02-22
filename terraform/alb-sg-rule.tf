# Security group rule to allow ALB to reach statistics-api pods
# Required because we disable manage-backend-security-group-rules in the ingress
# (AWS LBC expects exactly one SG tagged with cluster name, but EKS tags both cluster + node SGs)

resource "aws_security_group_rule" "alb_to_statistics_api" {
  type              = "ingress"
  from_port         = 8000
  to_port           = 8000
  protocol          = "tcp"
  security_group_id = module.eks.node_security_group_id
  description       = "Allow ALB to reach statistics-api on port 8000"

  # The ALB security group is created by AWS LBC dynamically
  # We use prefix list for ALB ranges as workaround (or could use 0.0.0.0/0 for simplicity)
  cidr_blocks = ["0.0.0.0/0"]
}
