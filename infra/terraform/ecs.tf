# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "traderx-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "traderx-${var.environment}"
  }
}

# IAM Execution Role
resource "aws_iam_role" "ecs_execution" {
  name = "traderx-${var.environment}-ecs-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "traderx-${var.environment}-ecs-exec"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "users_service" {
  name              = "/ecs/traderx-${var.environment}/users-service"
  retention_in_days = 7

  tags = {
    Service = "users-service"
  }
}

resource "aws_cloudwatch_log_group" "trades_service" {
  name              = "/ecs/traderx-${var.environment}/trades-service"
  retention_in_days = 7

  tags = {
    Service = "trades-service"
  }
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/traderx-${var.environment}/frontend"
  retention_in_days = 7

  tags = {
    Service = "frontend"
  }
}

# Task Definitions
resource "aws_ecs_task_definition" "users_service" {
  family                   = "traderx-users-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "users-service"
      image     = "${aws_ecr_repository.users_service.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = var.users_service_port
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "TENANT_ID", value = var.tenant_id },
        { name = "APP_PORT", value = tostring(var.users_service_port) },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "DATABASE_URL", value = "sqlite:////app/data/app_users.db" },
        { name = "TRADES_SERVICE_URL", value = "http://${aws_lb.main.dns_name}:80" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.users_service.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Service = "users-service"
  }
}

resource "aws_ecs_task_definition" "trades_service" {
  family                   = "traderx-trades-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "trades-service"
      image     = "${aws_ecr_repository.trades_service.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = var.trades_service_port
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "TENANT_ID", value = var.tenant_id },
        { name = "APP_PORT", value = tostring(var.trades_service_port) },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "DATABASE_URL", value = "sqlite:////app/data/app_trades.db" },
        { name = "USERS_SERVICE_URL", value = "http://${aws_lb.main.dns_name}:80" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.trades_service.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Service = "trades-service"
  }
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "traderx-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = var.frontend_port
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "TENANT_ID", value = var.tenant_id },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Service = "frontend"
  }
}

# ECS Services
resource "aws_ecs_service" "users_service" {
  name            = "traderx-users-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.users_service.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.users_service.arn
    container_name   = "users-service"
    container_port   = var.users_service_port
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Service = "users-service"
  }
}

resource "aws_ecs_service" "trades_service" {
  name            = "traderx-trades-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.trades_service.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.trades_service.arn
    container_name   = "trades-service"
    container_port   = var.trades_service_port
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Service = "trades-service"
  }
}

resource "aws_ecs_service" "frontend" {
  name            = "traderx-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.frontend_port
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Service = "frontend"
  }
}
