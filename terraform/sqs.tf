# SQS queue for Karpenter interruption handling.
# Karpenter watches this queue for AWS interruption events and drains
# affected nodes before they're actually terminated.
resource "aws_sqs_queue" "karpenter" {
  name = var.cluster_name

  # Messages older than 5 minutes are irrelevant — the interruption has already happened
  message_retention_seconds = 300

  # Encrypt messages at rest using the default SQS-managed key
  sqs_managed_sse_enabled = true

  tags = local.tags
}

# Queue policy — allows EventBridge and EC2 to publish interruption events to this queue
data "aws_iam_policy_document" "karpenter_sqs" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.karpenter.arn]

    principals {
      type = "Service"
      identifiers = [
        "events.amazonaws.com",
        "sqs.amazonaws.com",
      ]
    }
  }
}

resource "aws_sqs_queue_policy" "karpenter" {
  queue_url = aws_sqs_queue.karpenter.url
  policy    = data.aws_iam_policy_document.karpenter_sqs.json
}

# EventBridge rules — forward relevant AWS events to the SQS queue

# Spot interruption warning — EC2 sends this 2 minutes before terminating a Spot instance
resource "aws_cloudwatch_event_rule" "spot_interruption" {
  name        = "${var.cluster_name}-spot-interruption"
  description = "Karpenter: EC2 Spot Instance Interruption Warning"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Spot Instance Interruption Warning"]
  })

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "spot_interruption" {
  rule = aws_cloudwatch_event_rule.spot_interruption.name
  arn  = aws_sqs_queue.karpenter.arn
}

# Rebalance recommendation — EC2 hints that a Spot instance is at elevated interruption risk
resource "aws_cloudwatch_event_rule" "rebalance" {
  name        = "${var.cluster_name}-rebalance"
  description = "Karpenter: EC2 Instance Rebalance Recommendation"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Instance Rebalance Recommendation"]
  })

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "rebalance" {
  rule = aws_cloudwatch_event_rule.rebalance.name
  arn  = aws_sqs_queue.karpenter.arn
}

# Instance state change — catches unexpected terminations (stopping, shutting-down)
resource "aws_cloudwatch_event_rule" "instance_state_change" {
  name        = "${var.cluster_name}-instance-state-change"
  description = "Karpenter: EC2 Instance State-change Notification"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Instance State-change Notification"]
  })

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "instance_state_change" {
  rule = aws_cloudwatch_event_rule.instance_state_change.name
  arn  = aws_sqs_queue.karpenter.arn
}

# Scheduled change (AWS Health) — AWS maintenance events affecting instances
resource "aws_cloudwatch_event_rule" "scheduled_change" {
  name        = "${var.cluster_name}-scheduled-change"
  description = "Karpenter: AWS Health Event - Scheduled Change"

  event_pattern = jsonencode({
    source      = ["aws.health"]
    detail-type = ["AWS Health Event"]
  })

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "scheduled_change" {
  rule = aws_cloudwatch_event_rule.scheduled_change.name
  arn  = aws_sqs_queue.karpenter.arn
}
