# ============================================================
# Module: compute
# Creates an EC2 instance with a least-privilege security group.
# The instance lives in a private subnet by default.
# Callers specify what ports to open; everything else is denied.
# SSH is never opened to 0.0.0.0/0 — use SSM Session Manager.
# ============================================================

resource "aws_security_group" "app" {
  name        = "${var.name}-${var.environment}-app-sg"
  description = "Application security group for ${var.name} in ${var.environment}"
  vpc_id      = var.vpc_id

  # Only open the ports the caller explicitly requests
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description     = ingress.value.description
      from_port       = ingress.value.from_port
      to_port         = ingress.value.to_port
      protocol        = ingress.value.protocol
      cidr_blocks     = ingress.value.cidr_blocks
      security_groups = lookup(ingress.value, "security_groups", [])
    }
  }

  # Allow all outbound — instances need to reach package repos, AWS APIs, etc.
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-app-sg"
    Environment = var.environment
    Module      = "compute"
  })
}

resource "aws_instance" "app" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = var.iam_instance_profile

  # Never run as root. User data sets up the app as a non-root user.
  user_data = var.user_data

  # SSM agent for shell access without opening SSH
  # Requires AmazonSSMManagedInstanceCore policy on the instance role
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only — prevents SSRF credential theft
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size           = var.root_volume_size_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}"
    Environment = var.environment
    Module      = "compute"
  })
}
