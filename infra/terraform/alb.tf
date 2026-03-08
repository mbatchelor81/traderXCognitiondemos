resource "aws_lb" "traderx" {
  name               = "traderx-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name        = "traderx-${var.environment}-alb"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}

# Target group for users-service
resource "aws_lb_target_group" "users_service" {
  name        = "traderx-users-${var.environment}"
  port        = var.users_service_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.traderx.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name        = "traderx-users-${var.environment}"
    Environment = var.environment
  }
}

# Target group for trades-service
resource "aws_lb_target_group" "trades_service" {
  name        = "traderx-trades-${var.environment}"
  port        = var.trades_service_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.traderx.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name        = "traderx-trades-${var.environment}"
    Environment = var.environment
  }
}

# HTTP Listener with path-based routing
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.traderx.arn
  port              = 80
  protocol          = "HTTP"

  # Default action: forward to users-service
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }
}

# Path-based routing rule for trades-service
# Routes /trade*, /position*, /reference-data*, /socket.io* to trades-service
resource "aws_lb_listener_rule" "trades_service" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/trade*", "/position*", "/reference-data*", "/socket.io*", "/trades-service/*"]
    }
  }
}

# Path-based routing rule for users-service
# Routes /account*, /people*, /accountuser* to users-service
resource "aws_lb_listener_rule" "users_service" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }

  condition {
    path_pattern {
      values = ["/account*", "/people*", "/accountuser*", "/users-service/*"]
    }
  }
}

# Health check routing — direct /users-health and /trades-health
resource "aws_lb_listener_rule" "users_health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }

  condition {
    path_pattern {
      values = ["/users-service/health"]
    }
  }
}

resource "aws_lb_listener_rule" "trades_health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 11

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/trades-service/health"]
    }
  }
}
