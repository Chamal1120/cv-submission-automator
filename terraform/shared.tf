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

# S3 Bucket
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
  acl    = "private"
  depends_on = [aws_s3_bucket_ownership_controls.lambda_bucket_ownership]
}

resource "aws_s3_bucket_public_access_block" "lambda_bucket_access" {
  bucket = aws_s3_bucket.lambda_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

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
  depends_on = [aws_s3_bucket_public_access_block.lambda_bucket_access]
}

resource "aws_s3_bucket_cors_configuration" "lambda_bucket_cors" {
  bucket = aws_s3_bucket.lambda_bucket.id

  cors_rule {
    allowed_headers = ["*"] 
    allowed_methods = ["PUT"]
    allowed_origins = ["http://localhost:5173"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Shared IAM Role for CodeBuild
resource "aws_iam_role" "codebuild_role" {
  name = "cv-parser-codebuild-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "codebuild.amazonaws.com" }
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
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "lambda:UpdateFunctionCode"
        Resource = "arn:aws:lambda:${var.aws_region}:050752608379:function:*"
      }
    ]
  })
}

# Shared IAM Role for CodePipeline
resource "aws_iam_role" "codepipeline_role" {
  name = "cv-parser-codepipeline-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "codepipeline.amazonaws.com" }
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
          "codebuild:*",
          "lambda:*",
          "codestar-connections:UseConnection"
        ]
        Resource = "*"
      }
    ]
  })
}

# GitHub Connection (shared for all pipelines)
resource "aws_codestarconnections_connection" "github_connection" {
  name          = "cv-parser-github-connection"
  provider_type = "GitHub"
}
