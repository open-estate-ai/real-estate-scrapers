# ========================================
# ECR Repository
# ========================================

# ECR repository for the scraper Docker image
resource "aws_ecr_repository" "scraper" {
  name                 = "${lower(var.scraper_name)}-scraper"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Allow deletion even with images

  image_scanning_configuration {
    scan_on_push = false
  }
}


# ========================================
# App Runner Service
# ========================================

# IAM role for App Runner
resource "aws_iam_role" "app_runner_role" {
  name = "${local.resource_name_prefix_hyphenated}-runner-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

# Policy for App Runner to access ECR
resource "aws_iam_role_policy_attachment" "app_runner_ecr_access" {
  role       = aws_iam_role.app_runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# IAM role for App Runner instance (runtime access to AWS services)
resource "aws_iam_role" "app_runner_instance_role" {
  name = "${local.resource_name_prefix_hyphenated}-runner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

# Policy for App Runner instance to access Bedrock
resource "aws_iam_role_policy" "app_runner_instance_bedrock_access" {
  name = "${local.resource_name_prefix_hyphenated}-runner-instance-bedrock-policy"
  role = aws_iam_role.app_runner_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels"
        ]
        Resource = "*"
      }
    ]
  })
}


# Policy of App Runner instance to access S3
resource "aws_iam_role_policy" "app_runner_instance_s3_access" {
  name = "${local.resource_name_prefix_hyphenated}-runner-instance-s3-policy"
  role = aws_iam_role.app_runner_instance_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.raw_s3_bucket_scraper_data}",
          "arn:aws:s3:::${var.raw_s3_bucket_scraper_data}/${var.raw_s3_prefix_scraper_data}/*"
        ]
      }
    ]
  })
}

# App Runner service
resource "aws_apprunner_service" "scraper_service" {
  service_name = local.app_runner_service_name

  source_configuration {
    auto_deployments_enabled = false

    # Configure authentication for private ECR repository
    authentication_configuration {
      access_role_arn = aws_iam_role.app_runner_role.arn
    }

    image_repository {
      image_identifier = "${aws_ecr_repository.scraper.repository_url}:latest"
      image_configuration {
        port = "8080"
        runtime_environment_variables = {
          OPENAI_API_KEY  = var.openai_api_key
          LLM_MODEL       = var.bedrock_llm_model
          AWS_REGION_NAME = var.region
          S3_BUCKET       = var.raw_s3_bucket_scraper_data
          S3_PREFIX       = var.raw_s3_prefix_scraper_data


        }
      }
      image_repository_type = "ECR"
    }
  }

  instance_configuration {
    cpu               = "1 vCPU"
    memory            = "2 GB"
    instance_role_arn = aws_iam_role.app_runner_instance_role.arn
  }
}
