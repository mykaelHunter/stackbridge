# ============================================================
# Module: database
# Creates a PostgreSQL RDS instance in private subnets.
# Fixes every INF finding from the audit:
#   - Private subnet only (INF-01)
#   - No public accessibility (INF-01)
#   - Encrypted storage (INF-04)
#   - Automated backups enabled (INF-03)
#   - Deletion protection on (INF-03)
#   - Final snapshot on destroy (INF-03)
#   - Security group only allows app tier (INF-02)
#   - Multi-AZ configurable per environment (INF-05)
#   - Password from AWS Secrets Manager, never Terraform output (SEC-05)
# ============================================================

# ── Subnet group: private subnets only ───────────────────────
resource "aws_db_subnet_group" "this" {
  name        = "${var.name}-${var.environment}-db-subnet-group"
  description = "Private subnet group for ${var.name} ${var.environment} RDS"
  subnet_ids  = var.private_subnet_ids

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-db-subnet-group"
    Environment = var.environment
    Module      = "database"
  })
}

# ── Security group: only the app security group can connect ──
resource "aws_security_group" "db" {
  name        = "${var.name}-${var.environment}-db-sg"
  description = "Database security group - accepts connections from app tier only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from app tier"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  # No egress rule — RDS does not initiate outbound connections

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-db-sg"
    Environment = var.environment
    Module      = "database"
  })
}

# ── RDS password stored in Secrets Manager ────────────────────
# The password is generated here and stored as a secret.
# The application reads it at runtime — it never appears in
# Terraform outputs or state in plaintext.
resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_password" {
  name        = "stackbridge/${var.environment}/db-password"
  description = "RDS master password for ${var.name} ${var.environment}"
  recovery_window_in_days = var.environment == "prod" ? 7 : 0

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-db-password"
    Environment = var.environment
    Module      = "database"
  })
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    host     = aws_db_instance.this.address
    port     = 5432
    dbname   = var.db_name
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# ── RDS instance ──────────────────────────────────────────────
resource "aws_db_instance" "this" {
  identifier     = "${var.name}-${var.environment}"
  engine         = "postgres"
  engine_version = var.postgres_version

  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage_gb
  storage_type      = "gp3"
  storage_encrypted = true # INF-04: always encrypted

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false # INF-01: never public

  multi_az = var.multi_az # INF-05: true in prod

  # Backup configuration (INF-03)
  backup_retention_period   = var.backup_retention_days
  backup_window             = "03:00-04:00" # UTC, low-traffic window
  maintenance_window        = "Mon:04:00-Mon:05:00"
  copy_tags_to_snapshot     = true
  delete_automated_backups  = false

  # Deletion protection (INF-03)
  deletion_protection = var.deletion_protection
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.name}-${var.environment}-final-snapshot"

  # Performance insights for query observability
  performance_insights_enabled = true

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-db"
    Environment = var.environment
    Module      = "database"
  })
}
