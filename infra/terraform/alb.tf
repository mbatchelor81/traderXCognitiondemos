resource "aws_lb" "main" {
  name               = "traderx-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name = "traderx-${var.environment}-alb"
  }
}

# Target Groups
resource "aws_lb_target_group" "users_service" {
  name        = "traderx-users-${var.environment}"
  port        = var.users_service_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    port                = tostring(var.users_service_port)
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name = "traderx-users-${var.environment}"
  }
}

resource "aws_lb_target_group" "trades_service" {
  name        = "traderx-trades-${var.environment}"
  port        = var.trades_service_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    port                = tostring(var.trades_service_port)
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name = "traderx-trades-${var.environment}"
  }
}

resource "aws_lb_target_group" "frontend" {
  name        = "traderx-fe-${var.environment}"
  port        = var.frontend_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    port                = tostring(var.frontend_port)
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name = "traderx-fe-${var.environment}"
  }
}

# Listener — default action sends to frontend
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Path-based routing rules for users-service
# Routes: /account/, /accountuser/, /people/
resource "aws_lb_listener_rule" "users_service_account" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }

  condition {
    path_pattern {
      values = ["/account/*", "/account", "/accountuser/*", "/accountuser", "/people/*"]
    }
  }
}

resource "aws_lb_listener_rule" "users_service_health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 11

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }

  condition {
    path_pattern {
      values = ["/people"]
    }
  }
}

# Path-based routing rules for trades-service
# Routes: /trade/, /trades/, /positions/, /stocks/, /socket.io/
resource "aws_lb_listener_rule" "trades_service_trades" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/trade/*", "/trade", "/trades/*", "/trades", "/positions/*"]
    }
  }
}

resource "aws_lb_listener_rule" "trades_service_stocks" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 21

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/positions", "/stocks/*", "/stocks", "/socket.io/*", "/socket.io"]
    }
  }
}
