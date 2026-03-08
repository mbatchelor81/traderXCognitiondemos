resource "aws_lb" "main" {
  name               = "${local.app_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name = "${local.name_prefix}-alb"
  }
}

# Target Groups
resource "aws_lb_target_group" "users_service" {
  name        = "${local.app_name}-users-${var.environment}"
  port        = var.users_service_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Service = "users-service"
  }
}

resource "aws_lb_target_group" "trades_service" {
  name        = "${local.app_name}-trades-${var.environment}"
  port        = var.trades_service_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Service = "trades-service"
  }
}

resource "aws_lb_target_group" "web_frontend" {
  name        = "${local.app_name}-frontend-${var.environment}"
  port        = var.frontend_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Service = "web-frontend"
  }
}

# Listener — default action serves frontend
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_frontend.arn
  }
}

# ---- Users Service Routes ----
# Routes: /account/*, /accountuser/*, /people/*

resource "aws_lb_listener_rule" "users_account" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }

  condition {
    path_pattern {
      values = ["/account", "/account/*", "/accountuser", "/accountuser/*"]
    }
  }
}

resource "aws_lb_listener_rule" "users_people" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 110

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }

  condition {
    path_pattern {
      values = ["/people/*"]
    }
  }
}

# ---- Trades Service Routes ----
# Routes: /trade/*, /trades/*, /positions/*, /stocks/*

resource "aws_lb_listener_rule" "trades_trade" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/trade", "/trade/*", "/trades", "/trades/*"]
    }
  }
}

resource "aws_lb_listener_rule" "trades_positions" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 210

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/positions", "/positions/*"]
    }
  }
}

resource "aws_lb_listener_rule" "trades_stocks" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 220

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/stocks", "/stocks/*"]
    }
  }
}

# Socket.io routing for trades-service (trade feed)
resource "aws_lb_listener_rule" "trades_socketio" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 250

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.trades_service.arn
  }

  condition {
    path_pattern {
      values = ["/socket.io", "/socket.io/*"]
    }
  }
}
