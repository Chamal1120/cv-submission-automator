# terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.7.0"
}

provider "aws" {
  region = var.aws_region
}

# S3 Bucket for Lambda code and CV storage
resource "aws_s3_bucket" "lambda_bucket" {
  bucket_prefix = "cv-parser-lambda-"
  force_destroy = true
}

resource "aws_s3_bucket_ownership_controls" "lambda_bucket_ownership" {
  bucket = aws_s3_bucket.lambda_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "lambda_bucket_acl" {
  bucket = aws_s3_bucket.lambda_bucket.id
  acl    = "private"  # Bucket itself is private, objects are public via policy
  depends_on = [aws_s3_bucket_ownership_controls.lambda_bucket_ownership]
}

# Bucket Policy for Public Read Access
resource "aws_s3_bucket_policy" "public_read" {
  bucket = aws_s3_bucket.lambda_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.lambda_bucket.arn}/*"
      }
    ]
  })
}

# Package Lambda with uv
data "external" "lambda_build" {
  program = ["bash", "-c", <<EOT
    mkdir -p lambda_package
    cp ${path.module}/../lambda_function.py ${path.module}/../models/cv_parser.py lambda_package/
    uv pip install --python 3.12 -t lambda_package/ --no-deps ${path.module}/../
    cd lambda_package
    zip -r ../lambda_function.zip .
    echo "{\"output_path\": \"${path.module}/lambda_function.zip\", \"md5\": \"$(md5sum ${path.module}/lambda_function.zip | awk '{print $1}')\"}"
  EOT
  ]
}

resource "aws_s3_object" "lambda_code" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "lambda_function.zip"
  source = data.external.lambda_build.result.output_path
  etag   = data.external.lambda_build.result.md5
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "cv-parser-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "cv-parser-lambda-policy"
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.lambda_bucket.arn}/*"
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "cv_parser" {
  function_name    = "CVParserLambda"
  s3_bucket        = aws_s3_bucket.lambda_bucket.id
  s3_key           = aws_s3_object.lambda_code.key
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = data.external.lambda_build.result.md5
  timeout          = 30
  memory_size      = 256

  depends_on = [aws_s3_object.lambda_code]
}

# S3 Trigger
resource "aws_s3_bucket_notification" "lambda_trigger" {
  bucket = aws_s3_bucket.lambda_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.cv_parser.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".pdf"
  }
  depends_on = [aws_lambda_permission.s3_trigger]
}

resource "aws_lambda_permission" "s3_trigger" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cv_parser.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.lambda_bucket.arn
}

# IAM Roles for CodePipeline and CodeBuild
resource "aws_iam_role" "codepipeline_role" {
  name = "cv-parser-codepipeline-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "codepipeline.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "codepipeline_policy" {
  name = "cv-parser-codepipeline-policy"
  role = aws_iam_role.codepipeline_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*",
          "codecommit:*",
          "codebuild:*",
          "lambda:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "codebuild_role" {
  name = "cv-parser-codebuild-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "codebuild.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "codebuild_policy" {
  name = "cv-parser-codebuild-policy"
  role = aws_iam_role.codebuild_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:*",
          "s3:*",
          "codecommit:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# CodeBuild Project for Testing
resource "aws_codebuild_project" "test_project" {
  name          = "cv-parser-test"
  service_role  = aws_iam_role.codebuild_role.arn
  build_timeout = "10"

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:7.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
  }

  source {
    type            = "GITHUB"
    location        = "https://github.com/${var.github_owner}/${var.github_repo}.git"
    git_clone_depth = 1
    buildspec       = file("${path.module}/buildspec.yml")
  }
}

# CodePipeline
resource "aws_codepipeline" "cv_pipeline" {
  name     = "cv-parser-pipeline"
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = aws_s3_bucket.lambda_bucket.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source_output"]
      configuration = {
        Owner                = var.github_owner
        Repo                 = var.github_repo
        Branch               = "main"
        OAuthToken           = var.github_token
        PollForSourceChanges = "false"
      }
    }
  }

  stage {
    name = "Test"
    action {
      name            = "Test"
      category        = "Test"
      owner           = "AWS"
      provider        = "CodeBuild"
      input_artifacts = ["source_output"]
      version         = "1"
      configuration = {
        ProjectName = aws_codebuild_project.test_project.name
      }
    }
  }

  stage {
    name = "Deploy"
    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "Lambda"
      input_artifacts = ["source_output"]
      version         = "1"
      configuration = {
        FunctionName = aws_lambda_function.cv_parser.function_name
      }
    }
  }
}

resource "aws_codepipeline_webhook" "github_webhook" {
  name            = "cv-parser-webhook"
  authentication  = "GITHUB_HMAC"
  target_action   = "Source"
  target_pipeline = aws_codepipeline.cv_pipeline.name

  authentication_configuration {
    secret_token = var.github_webhook_secret
  }

  filter {
    json_path    = "$.ref"
    match_equals = "refs/heads/main"
  }
}

