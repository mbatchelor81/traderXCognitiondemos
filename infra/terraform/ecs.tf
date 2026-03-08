resource "aws_ecs_cluster" "traderx" {
  name = "traderx-${var.environment}"

  tags = {
    Name        = "traderx-${var.environment}"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}

# IAM execution role for ECS tasks
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

# CloudWatch log groups
resource "aws_cloudwatch_log_group" "users_service" {
  name              = "/ecs/traderx-users-service-${var.environment}"
  retention_in_days = 7

  tags = {
    Name        = "traderx-users-service-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "trades_service" {
  name              = "/ecs/traderx-trades-service-${var.environment}"
  retention_in_days = 7

  tags = {
    Name        = "traderx-trades-service-${var.environment}"
    Environment = var.environment
  }
}


# ECS Task Definitions
resource "aws_ecs_task_definition" "users_service" {
  family                   = "traderx-users-service-${var.environment}"
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
          hostPort      = var.users_service_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "TENANT_ID", value = var.tenant_id },
        { name = "APP_PORT", value = tostring(var.users_service_port) },
        { name = "APP_HOST", value = "0.0.0.0" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "TRADES_SERVICE_URL", value = "http://${aws_lb.traderx.dns_name}:80" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.users_service.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${var.users_service_port}/health')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }
    }
  ])

  tags = {
    Name        = "traderx-users-service-${var.environment}"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}

resource "aws_ecs_task_definition" "trades_service" {
  family                   = "traderx-trades-service-${var.environment}"
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
          hostPort      = var.trades_service_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "TENANT_ID", value = var.tenant_id },
        { name = "APP_PORT", value = tostring(var.trades_service_port) },
        { name = "APP_HOST", value = "0.0.0.0" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "USERS_SERVICE_URL", value = "http://${aws_lb.traderx.dns_name}:80" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.trades_service.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${var.trades_service_port}/health')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }
    }
  ])

  tags = {
    Name        = "traderx-trades-service-${var.environment}"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}

# ECS Services
resource "aws_ecs_service" "users_service" {
  name            = "traderx-users-service"
  cluster         = aws_ecs_cluster.traderx.id
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
    Name        = "traderx-users-service-${var.environment}"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}

resource "aws_ecs_service" "trades_service" {
  name            = "traderx-trades-service"
  cluster         = aws_ecs_cluster.traderx.id
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
    Name        = "traderx-trades-service-${var.environment}"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}
