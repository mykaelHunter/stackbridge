# ============================================================
# Module: network
# Creates a VPC with public and private subnets across two AZs,
# an internet gateway for public subnets, and NAT gateway so
# private resources can reach the internet for updates without
# being directly reachable from it.
#
# Callers never see routing tables, CIDR math, or IGW wiring.
# They provide a name, environment, and CIDR block.
# ============================================================

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name        = "${var.name}-vpc"
    Environment = var.environment
    Module      = "network"
  })
}

# ── Public subnets (one per AZ) ───────────────────────────────
resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = var.availability_zones[count.index]

  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name        = "${var.name}-public-${var.availability_zones[count.index]}"
    Environment = var.environment
    Tier        = "public"
    # EKS discovery tags — required for the AWS Load Balancer
    # Controller to auto-provision internet-facing ELBs/ALBs here,
    # and for the cluster to auto-discover this subnet.
    "kubernetes.io/role/elb"                      = "1"
    "kubernetes.io/cluster/${var.name}-${var.environment}" = "shared"
  })
}

# ── Private subnets (one per AZ) ─────────────────────────────
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.tags, {
    Name        = "${var.name}-private-${var.availability_zones[count.index]}"
    Environment = var.environment
    Tier        = "private"
    # EKS discovery tags — required for internal load balancers
    # and for worker nodes / pods to be scheduled in these subnets.
    "kubernetes.io/role/internal-elb"              = "1"
    "kubernetes.io/cluster/${var.name}-${var.environment}" = "shared"
  })
}

# ── Internet Gateway ──────────────────────────────────────────
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name        = "${var.name}-igw"
    Environment = var.environment
  })
}

# ── NAT Gateway (one, in first public subnet) ─────────────────
# Single NAT for cost efficiency in non-prod.
# Set nat_gateway_enabled = false in dev to save ~$30/month.
resource "aws_eip" "nat" {
  count  = var.nat_gateway_enabled ? 1 : 0
  domain = "vpc"

  tags = merge(var.tags, {
    Name        = "${var.name}-nat-eip"
    Environment = var.environment
  })
}

resource "aws_nat_gateway" "this" {
  count         = var.nat_gateway_enabled ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(var.tags, {
    Name        = "${var.name}-nat"
    Environment = var.environment
  })

  depends_on = [aws_internet_gateway.this]
}

# ── Route tables ──────────────────────────────────────────────
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-public-rt"
    Environment = var.environment
  })
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  dynamic "route" {
    for_each = var.nat_gateway_enabled ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.this[0].id
    }
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-private-rt"
    Environment = var.environment
  })
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
